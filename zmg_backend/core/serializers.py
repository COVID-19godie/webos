from rest_framework import serializers
# 🔴 注意：这里绝对不能导入 DesktopIcon，否则启动必闪退
from .models import (
    User, Resource, Category, Comment, Tenant, Membership, SyncPreference,
    AppEntry, AppTag, AppCollection, AppCollectionItem, AppComment
)
import uuid

# --- 基础序列化器 ---

class UserSerializer(serializers.ModelSerializer):
    class Meta: 
        model = User
        fields = ['id', 'username', 'role', 'avatar', 'score', 'bio']

class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'owner', 'is_active', 'created_at', 'updated_at']

class MembershipSerializer(serializers.ModelSerializer):
    tenant = TenantSerializer(read_only=True)
    class Meta:
        model = Membership
        fields = ['id', 'tenant', 'role', 'is_default', 'created_at']

class SyncPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncPreference
        fields = ['id', 'upload_enabled', 'conflict_strategy', 'last_sync_at', 'updated_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta: 
        model = Category
        fields = '__all__'

class ResourceSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    class Meta: 
        model = Resource
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta: 
        model = Comment
        fields = '__all__'

class AppTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppTag
        fields = ['id', 'name']

class AppEntrySerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    reviewed_by = UserSerializer(read_only=True)
    tags = AppTagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)
    comment_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AppEntry
        fields = [
            'id', 'title', 'summary', 'link', 'link_type', 'cover', 'icon_class',
            'status', 'author', 'tenant', 'tags', 'tag_names',
            'reviewed_by', 'review_reason', 'reviewed_at',
            'view_count', 'like_count', 'comment_count', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        app = AppEntry.objects.create(**validated_data)
        self._save_tags(app, tag_names)
        return app

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if tag_names is not None:
            instance.tags.clear()
            self._save_tags(instance, tag_names)
        return instance

    def _save_tags(self, app, tag_names):
        for name in tag_names:
            if not name: 
                continue
            tag, _ = AppTag.objects.get_or_create(name=name.strip()[:30])
            app.tags.add(tag)
        if tag_names is not None:
            tags_text = " ".join([t for t in tag_names if t]).strip()
            base = f"{app.title} {app.summary or ''} {tags_text}".strip()
            app.search_text = base
            app.save(update_fields=['search_text'])

class AppCollectionItemSerializer(serializers.ModelSerializer):
    app = AppEntrySerializer(read_only=True)
    class Meta:
        model = AppCollectionItem
        fields = ['id', 'app', 'order']

class AppCollectionSerializer(serializers.ModelSerializer):
    items = AppCollectionItemSerializer(many=True, read_only=True)
    class Meta:
        model = AppCollection
        fields = ['id', 'title', 'description', 'is_featured', 'items', 'created_at', 'updated_at']

class AppCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = AppComment
        fields = ['id', 'user', 'app', 'content', 'created_at']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta: 
        model = User
        fields = ('username', 'password', 'email')
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        tenant = Tenant.objects.create(
            name=f"{user.username} 的空间",
            slug=f"user-{user.id}-{uuid.uuid4().hex[:6]}",
            owner=user
        )
        Membership.objects.create(user=user, tenant=tenant, role='owner', is_default=True)
        return user

# --- 核心：桌面图标序列化 ---

class DesktopIconSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        # 🟢 必须在这里局部导入，解决闪退问题
        from .models import DesktopIcon
        model = DesktopIcon
        fields = '__all__'

    def get_type(self, obj):
        if not obj.content_type: return 'unknown'
        return obj.content_type.model 

    def get_data(self, obj):
        if not obj.content_object: return {}
        
        # 如果是文件
        if obj.content_type.model == 'resource':
            res = obj.content_object
            return {
                'id': res.id,
                'title': res.title,
                'cover': res.cover.url if res.cover else None,
                'kind': res.kind,
                'file': res.file.url if res.file else None,
                'link': res.link,
                'icon_class': res.icon_class 
            }
        # 如果是文件夹
        elif obj.content_type.model == 'category':
            cat = obj.content_object
            return {
                'id': cat.id,
                'name': cat.name,
                'icon': cat.icon,
                'icon_class': cat.icon 
            }
        return {}

    def get_preview(self, obj):
        """
        获取文件夹内部的前 4 个图标
        """
        if not obj.content_type or obj.content_type.model != 'category':
            return []
            
        cat = obj.content_object
        if not cat: 
            return []

        # 🟢 局部导入
        from .models import DesktopIcon
        children = DesktopIcon.objects.filter(parent_folder=cat).order_by('created_at')[:4]
        
        preview_list = []
        for child in children:
            item = {'type': 'unknown', 'cover': None}
            if child.content_type:
                item['type'] = child.content_type.model
                if child.content_type.model == 'resource':
                    res = child.content_object
                    if res and res.cover:
                        item['cover'] = res.cover.url
            preview_list.append(item)
            
        return preview_list