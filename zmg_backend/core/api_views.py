"""
API视图 - 支持前端通信
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from core.models import User, SyncPreference, DesktopIcon, Resource, Category, Membership
from core.tenant_utils import get_current_tenant, parse_client_datetime
from django.utils import timezone
import json
import os
import urllib.parse
import urllib.request

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """API登录接口 - 使用SimpleJWT"""
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'success': False,
                'detail': '用户名和密码不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        
        if user:
            # Ensure default entry icons on desktop
            try:
                membership = Membership.objects.filter(user=user, is_default=True).first()
                if not membership:
                    membership = Membership.objects.filter(user=user).first()
                tenant = membership.tenant if membership else None
                if tenant:
                    default_entries = [
                        {'title': '应用商店', 'link': '/store', 'icon': 'fa-solid fa-store', 'x': 80, 'y': 80},
                        {'title': '观看中心', 'link': '/watch', 'icon': 'fa-solid fa-circle-play', 'x': 80, 'y': 180},
                        {'title': '创作者中心', 'link': '/creator', 'icon': 'fa-solid fa-pen-nib', 'x': 80, 'y': 280},
                    ]
                    for entry in default_entries:
                        existing = DesktopIcon.objects.filter(
                            user=user,
                            tenant=tenant,
                            title=entry['title']
                        ).first()
                        if existing:
                            continue
                        res = Resource.objects.create(
                            title=entry['title'],
                            author=user,
                            tenant=tenant,
                            kind='link',
                            link=entry['link'],
                            icon_class=entry['icon'],
                            status='approved'
                        )
                        DesktopIcon.objects.create(
                            user=user,
                            tenant=tenant,
                            title=entry['title'],
                            content_object=res,
                            x=entry['x'],
                            y=entry['y'],
                            parent_folder=None
                        )
            except Exception:
                pass

            # 生成JWT token
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'username': user.username,
                'user_id': user.id,
                'role': user.role
            })
        else:
            return Response({
                'success': False,
                'detail': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)
            
    except Exception as e:
        return Response({
            'success': False,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    """API退出登录接口"""
    try:
        # JWT是无状态的，客户端只需删除token即可
        # 这里可以添加其他清理逻辑，如清除服务器端的刷新token等
        
        return Response({
            'success': True,
            'message': '退出登录成功'
        })
    except Exception as e:
        return Response({
            'success': False,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_user_info(request):
    """获取用户信息接口"""
    try:
        user = request.user
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_files_list(request):
    """获取文件列表接口"""
    try:
        # 这里应该从数据库或文件系统获取真实数据
        # 暂时返回模拟数据
        mock_files = [
            {
                'id': 1,
                'name': '工作报告.docx',
                'type': 'document',
                'size': 2048576,
                'modified': '2024-01-15T10:30:00Z',
                'path': '/documents/工作报告.docx'
            },
            {
                'id': 2,
                'name': '项目截图.png',
                'type': 'image',
                'size': 1024000,
                'modified': '2024-01-14T15:20:00Z',
                'path': '/images/项目截图.png'
            },
            {
                'id': 3,
                'name': '演示视频.mp4',
                'type': 'video',
                'size': 15728640,
                'modified': '2024-01-13T09:45:00Z',
                'path': '/videos/演示视频.mp4'
            },
            {
                'id': 4,
                'name': '音乐文件.mp3',
                'type': 'music',
                'size': 5242880,
                'modified': '2024-01-12T20:15:00Z',
                'path': '/music/音乐文件.mp3'
            }
        ]
        
        return Response({
            'success': True,
            'data': mock_files,
            'count': len(mock_files)
        })
    except Exception as e:
        return Response({
            'success': False,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_search(request):
    """搜索接口"""
    try:
        query = request.GET.get('q', '')
        
        if not query:
            return Response({
                'success': False,
                'detail': '搜索关键词不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 模拟搜索结果
        results = [
            {
                'id': 1,
                'name': f'{query}_相关文档.docx',
                'type': 'document',
                'relevance': 0.95
            }
        ]
        
        return Response({
            'success': True,
            'data': results,
            'query': query
        })
    except Exception as e:
        return Response({
            'success': False,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_upload_file(request):
    """文件上传接口"""
    try:
        if 'file' not in request.FILES:
            return Response({
                'success': False,
                'detail': '没有文件被上传'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # 这里应该处理文件保存逻辑
        # 暂时返回成功响应
        return Response({
            'success': True,
            'message': '文件上传成功',
            'data': {
                'filename': uploaded_file.name,
                'size': uploaded_file.size,
                'type': uploaded_file.content_type
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def health_check(request):
    """健康检查接口"""
    return JsonResponse({
        'status': 'healthy',
        'timestamp': '2024-01-15T10:00:00Z',
        'version': '1.0.0'
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_github_repos(request):
    """
    GitHub 仓库搜索代理（仅返回简化字段）
    """
    q = (request.GET.get('q') or '').strip()
    sort = (request.GET.get('sort') or 'stars').strip()
    order = (request.GET.get('order') or 'desc').strip()
    language = (request.GET.get('language') or '').strip()
    page = int(request.GET.get('page') or 1)
    per_page = min(int(request.GET.get('per_page') or 20), 50)

    query_parts = []
    if q:
        query_parts.append(q)
    if language:
        query_parts.append(f"language:{language}")
    if not query_parts:
        query_parts.append("stars:>500")
    query = " ".join(query_parts)

    params = {
        "q": query,
        "sort": sort,
        "order": order,
        "page": page,
        "per_page": per_page
    }
    url = f"https://api.github.com/search/repositories?{urllib.parse.urlencode(params)}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "zmg-webos",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return Response({"success": False, "detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

    items = []
    for repo in data.get("items", []):
        items.append({
            "id": repo.get("id"),
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "stars": repo.get("stargazers_count"),
            "html_url": repo.get("html_url"),
            "homepage": repo.get("homepage"),
            "owner": repo.get("owner", {}).get("login"),
            "owner_avatar": repo.get("owner", {}).get("avatar_url"),
            "topics": repo.get("topics", [])
        })

    return Response({
        "success": True,
        "total": data.get("total_count", 0),
        "items": items
    })

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_sync_settings(request):
    """同步设置：上传开关/冲突策略"""
    tenant = get_current_tenant(request)
    if not tenant:
        return Response({'success': False, 'detail': '未绑定租户'}, status=status.HTTP_403_FORBIDDEN)

    pref, _ = SyncPreference.objects.get_or_create(user=request.user, tenant=tenant)

    if request.method == 'PATCH':
        upload_enabled = request.data.get('upload_enabled')
        conflict_strategy = request.data.get('conflict_strategy')
        if upload_enabled is not None:
            pref.upload_enabled = bool(upload_enabled)
        if conflict_strategy in ['server_wins', 'client_wins']:
            pref.conflict_strategy = conflict_strategy
        pref.save()

    return Response({
        'success': True,
        'data': {
            'upload_enabled': pref.upload_enabled,
            'conflict_strategy': pref.conflict_strategy,
            'last_sync_at': pref.last_sync_at,
            'updated_at': pref.updated_at
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_sync_pull(request):
    """拉取云端变更"""
    tenant = get_current_tenant(request)
    if not tenant:
        return Response({'success': False, 'detail': '未绑定租户'}, status=status.HTTP_403_FORBIDDEN)

    since = parse_client_datetime(request.data.get('since'))
    icon_qs = DesktopIcon.objects.filter(user=request.user, tenant=tenant)
    res_qs = Resource.objects.filter(author=request.user, tenant=tenant)
    cat_qs = Category.objects.filter(tenant=tenant)

    if since:
        icon_qs = icon_qs.filter(updated_at__gt=since)
        res_qs = res_qs.filter(updated_at__gt=since)
        cat_qs = cat_qs.filter(updated_at__gt=since)

    icons = list(icon_qs.values(
        'id', 'title', 'x', 'y', 'parent_folder_id',
        'content_type_id', 'object_id', 'updated_at'
    ))
    resources = list(res_qs.values(
        'id', 'title', 'description', 'kind', 'link', 'icon_class',
        'category_id', 'updated_at'
    ))
    categories = list(cat_qs.values(
        'id', 'name', 'parent_id', 'icon', 'updated_at'
    ))

    return Response({
        'success': True,
        'data': {
            'icons': icons,
            'resources': resources,
            'categories': categories,
            'server_time': timezone.now()
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_sync_push(request):
    """推送本地变更（仅配置元数据）"""
    tenant = get_current_tenant(request)
    if not tenant:
        return Response({'success': False, 'detail': '未绑定租户'}, status=status.HTTP_403_FORBIDDEN)

    conflict_strategy = request.data.get('conflict_strategy', 'server_wins')
    icon_updates = request.data.get('icons', [])

    updated = 0
    skipped = 0

    for payload in icon_updates:
        icon_id = payload.get('id')
        if not icon_id:
            continue

        icon = DesktopIcon.objects.filter(id=icon_id, user=request.user, tenant=tenant).first()
        if not icon:
            continue

        client_updated_at = parse_client_datetime(payload.get('updated_at'))
        if (icon.updated_at and client_updated_at and
            icon.updated_at > client_updated_at and conflict_strategy == 'server_wins'):
            skipped += 1
            continue

        if 'x' in payload: icon.x = payload.get('x')
        if 'y' in payload: icon.y = payload.get('y')
        if 'parent_folder_id' in payload:
            icon.parent_folder_id = payload.get('parent_folder_id')
        if 'title' in payload:
            icon.title = payload.get('title')
        icon.save()
        updated += 1

    pref, _ = SyncPreference.objects.get_or_create(user=request.user, tenant=tenant)
    pref.last_sync_at = timezone.now()
    pref.save()

    return Response({
        'success': True,
        'data': {
            'updated': updated,
            'skipped': skipped,
            'server_time': pref.last_sync_at
        }
    })