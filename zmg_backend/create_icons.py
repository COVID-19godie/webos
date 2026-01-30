# create_icons.py
import os
import django

# 必须先设置环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zmg_backend.settings')
django.setup()

from core.models import User, Category, Resource, DesktopIcon
import random

def run():
    # 1. 获取当前用户
    user = User.objects.first() 
    if not user:
        print("❌ 错误：没有找到用户，请先创建管理员 (python manage.py createsuperuser)")
        return

    print(f"正在为用户 {user.username} 生成测试图标...")

    # 2. 创建测试文件夹
    for i in range(1, 4):
        name = f"测试文件夹_{i}"
        # get_or_create 防止重复创建报错
        cat, created = Category.objects.get_or_create(name=name, defaults={'icon': 'folder'})

        # 创建桌面图标
        DesktopIcon.objects.create(
            user=user,
            title=name,
            content_object=cat,
            x=50 + i * 100,
            y=50
        )
        print(f"✅ 文件夹图标: {name}")

    # 3. 创建测试文件
    for i in range(1, 6):
        title = f"文档_{i}.txt"
        res, created = Resource.objects.get_or_create(
            title=title,
            defaults={
                'author': user,
                'kind': 'doc',
                'icon_class': 'fa-solid fa-file-lines'
            }
        )

        DesktopIcon.objects.create(
            user=user,
            title=title,
            content_object=res,
            x=50 + i * 100,
            y=150
        )
        print(f"✅ 文件图标: {title}")

    print("\n🎉 全部完成！")

if __name__ == '__main__':
    run()