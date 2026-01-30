from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import uuid

# 1. 定义动态路径生成函数
def resource_directory_path(instance, filename):
    # 获取当前日期
    today = timezone.now()
    # 生成路径: resources/2026/01/26/uuid_filename
    # 使用 uuid 避免文件名冲突，保留原始扩展名
    ext = filename.split('.')[-1]
    new_filename = f"{uuid.uuid4().hex[:10]}_{filename}"
    return f'resources/{today.year}/{today.month}/{today.day}/{new_filename}'

# 1. 用户模型
class User(AbstractUser):
    ROLE_CHOICES = (('student', '学生'), ('teacher', '教师'), ('admin', '管理员'))
    role = models.CharField("角色", max_length=10, choices=ROLE_CHOICES, default='student')
    avatar = models.ImageField("头像", upload_to='avatars/', null=True, blank=True)
    score = models.IntegerField("积分", default=0)
    bio = models.TextField("个人简介", blank=True)
    class Meta: verbose_name = "用户"

# 1.1 多租户
class Tenant(models.Model):
    name = models.CharField("租户名称", max_length=100)
    slug = models.SlugField("租户标识", max_length=100, unique=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_tenants')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.name
    class Meta: verbose_name = "租户"

class Membership(models.Model):
    ROLE_CHOICES = (
        ('owner', '所有者'),
        ('admin', '租户管理员'),
        ('member', '普通成员'),
        ('viewer', '访客')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField("成员角色", max_length=10, choices=ROLE_CHOICES, default='member')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "成员关系"
        unique_together = ('user', 'tenant')

class SyncPreference(models.Model):
    CONFLICT_CHOICES = (
        ('server_wins', '以云端为准'),
        ('client_wins', '以本地为准')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sync_preferences')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='sync_preferences')
    upload_enabled = models.BooleanField(default=False)
    conflict_strategy = models.CharField(max_length=20, choices=CONFLICT_CHOICES, default='server_wins')
    last_sync_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "同步偏好"
        unique_together = ('user', 'tenant')

# 2. 分类模型
class Category(models.Model):
    name = models.CharField("分类名称", max_length=50)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    icon = models.CharField("图标", max_length=50, default="folder")
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return self.name
    class Meta: verbose_name = "资源分类"

# 3. 资源模型
class Resource(models.Model):
    STATUS_CHOICES = (('pending', '待审核'), ('approved', '已发布'))
    KIND_CHOICES = (
        ('doc', '文档'), 
        ('video', '视频'), 
        ('image', '图片'), 
        ('audio', '音频'), 
        ('archive', '压缩包'), 
        ('link', '链接'), 
        ('other', '其他')
    )
    
    title = models.CharField("标题", max_length=100)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='resources', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    # 修改 file 字段，使用上面定义的函数
    file = models.FileField(upload_to=resource_directory_path, null=True, blank=True, verbose_name="资源文件")
    link = models.URLField(null=True, blank=True)
    # [新增] 图标类名字段 (用于存储 FontAwesome 类名，例如 'fa-solid fa-file-pdf')
    icon_class = models.CharField("图标类名", max_length=50, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='approved')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_tags = models.CharField("AI标签", max_length=200, blank=True)
    embedding_text = models.TextField("向量文本", null=True, blank=True)

    # 修改 save 方法，自动根据后缀赋予默认图标
    def save(self, *args, **kwargs):
        if(self.file or self.link) and self.kind == 'other': # 简单的自动分类逻辑
            name = self.file.name if self.file else self.link
            ext = name.split('.')[-1].lower() if '.' in name else ''
            
            # 增强的类型判断
            if ext in ['mp4','mov','avi','mkv']: self.kind = 'video'
            elif ext in ['jpg','jpeg','png','gif','webp','bmp']: self.kind = 'image'
            elif ext in ['mp3','wav','flac','m4a']: self.kind = 'audio'
            elif ext in ['zip','rar','7z','tar','gz']: self.kind = 'archive'
            elif ext in ['pdf','doc','docx','xls','xlsx','ppt','pptx','txt','md']: self.kind = 'doc'
            
            # 自动图标 (增加图片/音频支持)
            if not self.icon_class:
                if self.kind == 'image': self.icon_class = 'fa-solid fa-file-image'
                elif self.kind == 'audio': self.icon_class = 'fa-solid fa-file-audio'
                elif self.kind == 'video': self.icon_class = 'fa-solid fa-file-video'
                elif self.kind == 'archive': self.icon_class = 'fa-solid fa-file-zipper'
                elif ext == 'pdf': self.icon_class = 'fa-solid fa-file-pdf'
                elif ext in ['doc', 'docx']: self.icon_class = 'fa-solid fa-file-word'
                elif ext in ['xls', 'xlsx']: self.icon_class = 'fa-solid fa-file-excel'
                elif ext in ['ppt', 'pptx']: self.icon_class = 'fa-solid fa-file-powerpoint'
                elif ext in ['py', 'js', 'html', 'css']: self.icon_class = 'fa-solid fa-file-code'
                elif self.kind == 'link': self.icon_class = 'fa-solid fa-link'
                else: self.icon_class = 'fa-solid fa-file'
                
        super().save(*args, **kwargs)

# 4. [新增] 桌面图标模型 (核心)
class DesktopIcon(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='desktop_icons')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='desktop_icons', null=True, blank=True)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    title = models.CharField("显示名称", max_length=100)
    
    # 泛型关联：指向文件或文件夹
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    parent_folder = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='icons_inside')
    is_shortcut = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta: ordering = ['created_at']

# 5. 评论模型
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField("评论内容")
    created_at = models.DateTimeField(auto_now_add=True)

# 6. 应用商店（仅存链接）
class AppTag(models.Model):
    name = models.CharField("标签", max_length=30, unique=True)
    def __str__(self): return self.name
    class Meta: verbose_name = "应用标签"

class AppEntry(models.Model):
    STATUS_CHOICES = (
        ('pending', '待审核'),
        ('approved', '已上架'),
        ('rejected', '已拒绝')
    )
    TYPE_CHOICES = (
        ('h5', 'H5应用'),
        ('video', '视频链接'),
        ('doc', '文章/文档'),
        ('image', '图片集'),
        ('other', '其他')
    )
    title = models.CharField("标题", max_length=120)
    summary = models.CharField("简介", max_length=200, blank=True)
    link = models.URLField("链接")
    link_type = models.CharField("类型", max_length=10, choices=TYPE_CHOICES, default='h5')
    cover = models.ImageField(upload_to='app_covers/', null=True, blank=True)
    icon_class = models.CharField("图标类名", max_length=50, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_entries')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='app_entries', null=True, blank=True)
    tags = models.ManyToManyField(AppTag, blank=True, related_name='apps')
    search_text = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_apps')
    review_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.search_text:
            base = f"{self.title} {self.summary or ''}".strip()
            self.search_text = base
        super().save(*args, **kwargs)

    def __str__(self): return self.title
    class Meta: verbose_name = "应用条目"

class AppCollection(models.Model):
    title = models.CharField("专题标题", max_length=100)
    description = models.TextField("专题描述", blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='collections', null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self): return self.title
    class Meta: verbose_name = "专题合集"

class AppCollectionItem(models.Model):
    collection = models.ForeignKey(AppCollection, on_delete=models.CASCADE, related_name='items')
    app = models.ForeignKey(AppEntry, on_delete=models.CASCADE, related_name='collection_items')
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "专题条目"
        unique_together = ('collection', 'app')

class AppComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(AppEntry, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField("评论内容")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: verbose_name = "应用评论"

class AppLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(AppEntry, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "应用点赞"
        unique_together = ('user', 'app')

class AppReport(models.Model):
    REASON_CHOICES = (
        ('spam', '垃圾信息'),
        ('copyright', '侵权'),
        ('abuse', '恶意内容'),
        ('other', '其他')
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app = models.ForeignKey(AppEntry, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='other')
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: verbose_name = "应用举报"

class AppView(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    app = models.ForeignKey(AppEntry, on_delete=models.CASCADE, related_name='views')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta: verbose_name = "应用浏览"