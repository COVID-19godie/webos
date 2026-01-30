from rest_framework import viewsets, permissions, filters, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import Q
from django.db import models
from django.utils import timezone
import os
import shutil
import random
from .models import (
    Resource, Category, User, Comment, DesktopIcon, Tenant, Membership,
    AppEntry, AppTag, AppCollection, AppCollectionItem, AppComment, AppLike, AppReport, AppView
)
from .serializers import (
    ResourceSerializer, CategorySerializer, UserSerializer, RegisterSerializer,
    CommentSerializer, DesktopIconSerializer, TenantSerializer, MembershipSerializer,
    AppEntrySerializer, AppTagSerializer, AppCollectionSerializer, AppCommentSerializer
)
from .tenant_utils import get_current_tenant, get_current_membership

# --- 辅助函数：安全获取整数坐标 ---
def get_safe_coord(data, key, default_min=50, default_max=400):
    try:
        val = data.get(key)
        if val is None:
            return random.randint(default_min, default_max)
        return int(float(val))
    except (ValueError, TypeError):
        return random.randint(default_min, default_max)

# --- 基础视图 ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant(self.request)
        if not tenant:
            return Category.objects.none()
        return Category.objects.filter(tenant=tenant)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        tenant = get_current_tenant(self.request)
        if not tenant:
            return Resource.objects.none()
        membership = get_current_membership(self.request)
        if membership and membership.role in ['owner', 'admin']:
            return Resource.objects.filter(tenant=tenant)
        return Resource.objects.filter(tenant=tenant, author=self.request.user)

    def perform_create(self, serializer):
        tenant = get_current_tenant(self.request)
        serializer.save(author=self.request.user, tenant=tenant)
    
    @action(detail=True, methods=['POST'])
    def view(self, request, pk=None):
        return Response({'status': 'ok'})
        
    @action(detail=True, methods=['POST'])
    def comment(self, request, pk=None):
        Comment.objects.create(
            user=request.user, 
            resource=self.get_object(), 
            content=request.data.get('content')
        )
        return Response({'status': 'success'})
        
    @action(detail=True, methods=['GET'])
    def comments(self, request, pk=None):
        return Response(CommentSerializer(self.get_object().comments.all(), many=True).data)

# --- 核心：桌面图标视图 ---

class DesktopIconViewSet(viewsets.ModelViewSet):
    serializer_class = DesktopIconSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        parent_id = self.request.query_params.get('parent_id')
        user = self.request.user
        tenant = get_current_tenant(self.request)
        if not tenant:
            return DesktopIcon.objects.none()

        qs = DesktopIcon.objects.filter(user=user, tenant=tenant)

        if self.action in ['retrieve', 'update', 'partial_update', 'destroy', 'uninstall', 'rename', 'move', 'change_icon']:
            return qs

        if parent_id == 'root' or not parent_id:
            return qs.filter(parent_folder__isnull=True)
        elif parent_id == 'recent':
            return qs.order_by('-created_at')[:20]
        elif parent_id in ['image', 'doc', 'video', 'audio']:
            resource_ct = ContentType.objects.get_for_model(Resource)
            target_resources = Resource.objects.filter(kind=parent_id).values('id')
            return qs.filter(
                content_type=resource_ct,
                object_id__in=target_resources
            )
        else:
            return qs.filter(parent_folder_id=parent_id)
            
    @action(detail=True, methods=['PATCH'])
    def move(self, request, pk=None):
        icon = self.get_object()
        
        if 'x' in request.data:
            icon.x = get_safe_coord(request.data, 'x', 0, 0)
        if 'y' in request.data:
            icon.y = get_safe_coord(request.data, 'y', 0, 0)
            
        if 'parent_id' in request.data:
            pid = request.data['parent_id']
            if pid == 'root' or pid is None:
                icon.parent_folder = None
            else:
                icon.parent_folder_id = pid
                
        icon.save()
        return Response({'status': 'moved'})

    @action(detail=False, methods=['POST'])
    def create_folder(self, request):
        user = request.user
        name = request.data.get('name', '新建文件夹')
        x = get_safe_coord(request.data, 'x')
        y = get_safe_coord(request.data, 'y')
        tenant = get_current_tenant(request)
        
        parent_id = request.data.get('parent_id')
        if parent_id == 'root': parent_id = None
        if not tenant:
            return Response({'status': 'error', 'msg': '未绑定租户'}, status=403)

        real_folder = Category.objects.create(name=name, parent_id=parent_id, icon='folder', tenant=tenant)
        
        icon = DesktopIcon.objects.create(
            user=user, 
            title=name, 
            content_object=real_folder, 
            x=x, y=y, 
            parent_folder_id=parent_id,
            tenant=tenant
        )
        return Response(DesktopIconSerializer(icon).data)

    @action(detail=False, methods=['POST'], parser_classes=[MultiPartParser, FormParser])
    def upload_file(self, request):
        user = request.user
        file_obj = request.FILES.get('file')
        tenant = get_current_tenant(request)
        
        if not file_obj:
            return Response({'status': 'error', 'msg': '未接收到文件数据'}, status=400)
        if not tenant:
            return Response({'status': 'error', 'msg': '未绑定租户'}, status=403)

        x = get_safe_coord(request.data, 'x')
        y = get_safe_coord(request.data, 'y')
        parent_id = request.data.get('parent_id')
        
        current_parent_cat = None
        if parent_id and parent_id != 'root':
            try:
                current_parent_cat = Category.objects.get(id=parent_id)
            except Category.DoesNotExist:
                pass

        try:
            res = Resource.objects.create(
                title=file_obj.name, 
                author=user, 
                tenant=tenant,
                file=file_obj, 
                category=current_parent_cat, 
                status='approved'
            )
            
            icon = DesktopIcon.objects.create(
                user=user, 
                title=res.title, 
                content_object=res, 
                x=x, y=y,
                parent_folder=current_parent_cat,
                tenant=tenant
            )
            return Response(DesktopIconSerializer(icon).data)
        except Exception as e:
            return Response({'status': 'error', 'msg': str(e)}, status=500)

    @action(detail=True, methods=['POST'])
    def rename(self, request, pk=None):
        icon = self.get_object()
        new_name = request.data.get('name')
        if new_name:
            icon.title = new_name
            icon.save()
            if icon.content_object:
                if hasattr(icon.content_object, 'title'):
                    icon.content_object.title = new_name
                    icon.content_object.save()
                elif hasattr(icon.content_object, 'name'):
                    icon.content_object.name = new_name
                    icon.content_object.save()
        return Response({'status': 'renamed'})

    @action(detail=True, methods=['POST'])
    def change_icon(self, request, pk=None):
        icon = self.get_object()
        new_icon_class = request.data.get('icon_class')
        
        if not new_icon_class:
            return Response({'status': 'error', 'msg': '图标参数为空'}, status=400)

        obj = icon.content_object
        if isinstance(obj, Resource):
            obj.icon_class = new_icon_class
            obj.save()
        elif isinstance(obj, Category):
            obj.icon = new_icon_class
            obj.save()
            
        return Response({'status': 'success', 'msg': '图标已更新'})

    @action(detail=False, methods=['POST'])
    def create_link(self, request):
        user = request.user
        title = request.data.get('title')
        link = request.data.get('link')
        icon_class = request.data.get('icon_class')
        x = get_safe_coord(request.data, 'x')
        y = get_safe_coord(request.data, 'y')
        parent_id = request.data.get('parent_id')
        if parent_id == 'root': parent_id = None
        tenant = get_current_tenant(request)
        if not tenant:
            return Response({'status': 'error', 'msg': '未绑定租户'}, status=403)

        res = Resource.objects.create(
            title=title, author=user, link=link, kind='link',
            icon_class=icon_class, status='approved', tenant=tenant
        )

        icon = DesktopIcon.objects.create(
            user=user, title=res.title, content_object=res,
            x=x, y=y, parent_folder_id=parent_id, tenant=tenant
        )
        return Response(DesktopIconSerializer(icon).data)

    @action(detail=False, methods=['POST'])
    def create_html_file(self, request):
        user = request.user
        title = request.data.get('title', '未命名文档')
        content = request.data.get('content', '<h1>Hello World</h1>')
        x = get_safe_coord(request.data, 'x')
        y = get_safe_coord(request.data, 'y')
        tenant = get_current_tenant(request)
        if not tenant:
            return Response({'status': 'error', 'msg': '未绑定租户'}, status=403)

        file_content = ContentFile(content.encode('utf-8'))
        file_name = f"{title}.html"
        
        res = Resource.objects.create(
            title=title, author=user, kind='doc',
            icon_class='fa-brands fa-html5', status='approved', tenant=tenant
        )
        res.file.save(file_name, file_content)
        
        icon = DesktopIcon.objects.create(
            user=user, title=title, content_object=res,
            x=x, y=y, parent_folder_id=request.data.get('parent_id'), tenant=tenant
        )
        return Response(DesktopIconSerializer(icon).data)

    @action(detail=False, methods=['POST'], parser_classes=[MultiPartParser, FormParser])
    def install_h5_app(self, request):
        user = request.user
        file_obj = request.FILES.get('file')
        title = request.data.get('title', '未命名应用')
        icon_class = request.data.get('icon_class', 'fa-brands fa-html5')
        x = get_safe_coord(request.data, 'x')
        y = get_safe_coord(request.data, 'y')
        tenant = get_current_tenant(request)
        
        if not file_obj: return Response({'status': 'error', 'msg': '未上传文件'}, status=400)
        if not tenant:
            return Response({'status': 'error', 'msg': '未绑定租户'}, status=403)

        filename = file_obj.name.lower()
        if not filename.endswith('.zip'):
            return Response({'status': 'error', 'msg': '仅支持上传ZIP包'}, status=400)

        res = Resource.objects.create(
            title=title, author=user, kind='archive',
            icon_class=icon_class, status='approved', tenant=tenant
        )
        res.file.save(file_obj.name, file_obj)
        
        parent_id = request.data.get('parent_id')
        if parent_id == 'root': parent_id = None

        icon = DesktopIcon.objects.create(
            user=user, title=title, content_object=res,
            x=x, y=y, parent_folder_id=parent_id, tenant=tenant
        )

        return Response({'status': 'success', 'data': DesktopIconSerializer(icon).data})

    @action(detail=True, methods=['DELETE'])
    def uninstall(self, request, pk=None):
        try:
            icon = self.get_object()
            if icon.user != request.user:
                return Response({'status': 'error', 'msg': '无权删除'}, status=403)

            obj = icon.content_object
            if obj:
                if isinstance(obj, Category):
                    DesktopIcon.objects.filter(parent_folder=obj).delete()
                    obj.delete()
                elif isinstance(obj, Resource):
                    if obj.file:
                        try:
                            obj.file.delete(save=False)
                        except:
                            pass
                    if obj.kind == 'link' and obj.link and '/h5apps/' in obj.link:
                        try:
                            media_path = obj.link.replace(settings.MEDIA_URL, '')
                            if media_path.startswith('/'): media_path = media_path[1:]
                            parts = media_path.split('/')
                            if len(parts) >= 2 and parts[0] == 'h5apps':
                                app_root = os.path.join(settings.MEDIA_ROOT, 'h5apps', parts[1])
                                if os.path.exists(app_root): shutil.rmtree(app_root)
                        except: pass
                    obj.delete()
            
            icon.delete()
            return Response({'status': 'success'})

        except DesktopIcon.DoesNotExist:
            return Response({'status': 'error', 'msg': '图标不存在'}, status=404)
        except Exception as e:
            return Response({'status': 'error', 'msg': str(e)}, status=500)

# --- 多租户/成员 ---

class TenantViewSet(viewsets.ModelViewSet):
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Tenant.objects.filter(memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        tenant = serializer.save(owner=self.request.user)
        Membership.objects.create(user=self.request.user, tenant=tenant, role='owner', is_default=True)

class MembershipViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Membership.objects.filter(user=self.request.user).select_related('tenant')

# --- 应用商店 ---

def is_tenant_admin(request):
    membership = get_current_membership(request)
    return membership and membership.role in ['owner', 'admin']

class AppTagViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AppTagSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AppTag.objects.all().order_by('name')

class AppEntryViewSet(viewsets.ModelViewSet):
    serializer_class = AppEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant(self.request)
        if not tenant:
            return AppEntry.objects.none()
        qs = AppEntry.objects.filter(tenant=tenant)
        status = self.request.query_params.get('status')
        if not is_tenant_admin(self.request):
            if self.action == 'list':
                qs = qs.filter(status='approved')
            else:
                qs = qs.filter(
                    Q(status='approved') | Q(author=self.request.user)
                )
        elif status in ['pending', 'approved', 'rejected']:
            qs = qs.filter(status=status)
        search = self.request.query_params.get('search')
        link_type = self.request.query_params.get('link_type')
        tag_names = self.request.query_params.get('tags')
        if search:
            qs = qs.filter(
                Q(search_text__icontains=search) |
                Q(title__icontains=search) |
                Q(summary__icontains=search)
            )
        if link_type:
            qs = qs.filter(link_type=link_type)
        if tag_names:
            names = [n.strip() for n in tag_names.split(',') if n.strip()]
            if names:
                qs = qs.filter(tags__name__in=names).distinct()
        return qs.annotate(comment_count=models.Count('comments')).order_by('-created_at')

    def perform_create(self, serializer):
        tenant = get_current_tenant(self.request)
        status = 'approved' if is_tenant_admin(self.request) else 'pending'
        serializer.save(author=self.request.user, tenant=tenant, status=status)

    @action(detail=False, methods=['GET'])
    def mine(self, request):
        tenant = get_current_tenant(request)
        if not tenant:
            return Response([])
        qs = AppEntry.objects.filter(tenant=tenant, author=request.user).annotate(
            comment_count=models.Count('comments')
        ).order_by('-created_at')
        return Response(AppEntrySerializer(qs, many=True).data)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk=None):
        if not is_tenant_admin(request):
            return Response({'status': 'error', 'msg': '无权限'}, status=403)
        app = self.get_object()
        app.status = 'approved'
        app.reviewed_by = request.user
        app.review_reason = request.data.get('reason', '')
        app.reviewed_at = timezone.now()
        app.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk=None):
        if not is_tenant_admin(request):
            return Response({'status': 'error', 'msg': '无权限'}, status=403)
        app = self.get_object()
        app.status = 'rejected'
        app.reviewed_by = request.user
        app.review_reason = request.data.get('reason', '')
        app.reviewed_at = timezone.now()
        app.save()
        return Response({'status': 'success'})

    @action(detail=True, methods=['POST'])
    def like(self, request, pk=None):
        app = self.get_object()
        obj, created = AppLike.objects.get_or_create(user=request.user, app=app)
        if created:
            app.like_count = AppLike.objects.filter(app=app).count()
            app.save()
        return Response({'status': 'success', 'like_count': app.like_count})

    @action(detail=True, methods=['DELETE'])
    def unlike(self, request, pk=None):
        app = self.get_object()
        AppLike.objects.filter(user=request.user, app=app).delete()
        app.like_count = AppLike.objects.filter(app=app).count()
        app.save()
        return Response({'status': 'success', 'like_count': app.like_count})

    @action(detail=True, methods=['POST'])
    def view(self, request, pk=None):
        app = self.get_object()
        AppView.objects.create(user=request.user, app=app)
        app.view_count = AppView.objects.filter(app=app).count()
        app.save()
        return Response({'status': 'success', 'view_count': app.view_count})

    @action(detail=True, methods=['POST'])
    def comment(self, request, pk=None):
        app = self.get_object()
        content = request.data.get('content')
        if not content:
            return Response({'status': 'error', 'msg': '评论不能为空'}, status=400)
        AppComment.objects.create(user=request.user, app=app, content=content)
        return Response({'status': 'success'})

    @action(detail=True, methods=['GET'])
    def comments(self, request, pk=None):
        app = self.get_object()
        qs = app.comments.select_related('user').order_by('-created_at')
        return Response(AppCommentSerializer(qs, many=True).data)

    @action(detail=True, methods=['POST'])
    def report(self, request, pk=None):
        app = self.get_object()
        reason = request.data.get('reason', 'other')
        detail = request.data.get('detail', '')
        AppReport.objects.create(user=request.user, app=app, reason=reason, detail=detail)
        return Response({'status': 'success'})

    @action(detail=False, methods=['POST'])
    def bulk_approve(self, request):
        if not is_tenant_admin(request):
            return Response({'status': 'error', 'msg': '无权限'}, status=403)
        tenant = get_current_tenant(request)
        ids = request.data.get('ids', [])
        reason = request.data.get('reason', '')
        qs = AppEntry.objects.filter(tenant=tenant, id__in=ids)
        qs.update(
            status='approved',
            reviewed_by=request.user,
            review_reason=reason,
            reviewed_at=timezone.now()
        )
        return Response({'status': 'success', 'count': qs.count()})

    @action(detail=False, methods=['POST'])
    def bulk_reject(self, request):
        if not is_tenant_admin(request):
            return Response({'status': 'error', 'msg': '无权限'}, status=403)
        tenant = get_current_tenant(request)
        ids = request.data.get('ids', [])
        reason = request.data.get('reason', '')
        qs = AppEntry.objects.filter(tenant=tenant, id__in=ids)
        qs.update(
            status='rejected',
            reviewed_by=request.user,
            review_reason=reason,
            reviewed_at=timezone.now()
        )
        return Response({'status': 'success', 'count': qs.count()})

class AppCollectionViewSet(viewsets.ModelViewSet):
    serializer_class = AppCollectionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = get_current_tenant(self.request)
        if not tenant:
            return AppCollection.objects.none()
        qs = AppCollection.objects.filter(tenant=tenant)
        if not is_tenant_admin(self.request):
            qs = qs.filter(is_featured=True)
        return qs.order_by('-updated_at')

    def perform_create(self, serializer):
        tenant = get_current_tenant(self.request)
        serializer.save(owner=self.request.user, tenant=tenant)

    @action(detail=True, methods=['POST'])
    def add_item(self, request, pk=None):
        if not is_tenant_admin(request):
            return Response({'status': 'error', 'msg': '无权限'}, status=403)
        collection = self.get_object()
        app_id = request.data.get('app_id')
        order = request.data.get('order', 0)
        if not app_id:
            return Response({'status': 'error', 'msg': 'app_id缺失'}, status=400)
        app = AppEntry.objects.filter(id=app_id, tenant=collection.tenant).first()
        if not app:
            return Response({'status': 'error', 'msg': '应用不存在'}, status=404)
        AppCollectionItem.objects.update_or_create(collection=collection, app=app, defaults={'order': order})
        return Response({'status': 'success'})

    @action(detail=True, methods=['POST'])
    def reorder(self, request, pk=None):
        if not is_tenant_admin(request):
            return Response({'status': 'error', 'msg': '无权限'}, status=403)
        collection = self.get_object()
        items = request.data.get('items', [])
        for item in items:
            item_id = item.get('id')
            order = item.get('order', 0)
            if not item_id:
                continue
            AppCollectionItem.objects.filter(
                id=item_id,
                collection=collection
            ).update(order=order)
        return Response({'status': 'success'})