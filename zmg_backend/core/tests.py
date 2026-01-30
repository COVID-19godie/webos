from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from rest_framework.test import APIClient
from django.utils import timezone
from .models import User, Tenant, Membership, Category, DesktopIcon, SyncPreference

class TenantSyncTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='u1', password='pass123')
        self.user2 = User.objects.create_user(username='u2', password='pass123')

        self.tenant1 = Tenant.objects.create(name='T1', slug='t1', owner=self.user)
        self.tenant2 = Tenant.objects.create(name='T2', slug='t2', owner=self.user2)

        Membership.objects.create(user=self.user, tenant=self.tenant1, role='owner', is_default=True)
        Membership.objects.create(user=self.user2, tenant=self.tenant2, role='owner', is_default=True)

    def test_tenant_scoped_desktop_icons(self):
        cat1 = Category.objects.create(name='C1', tenant=self.tenant1)
        cat2 = Category.objects.create(name='C2', tenant=self.tenant2)
        ct = ContentType.objects.get_for_model(Category)

        DesktopIcon.objects.create(
            user=self.user, tenant=self.tenant1, title='I1',
            content_type=ct, object_id=cat1.id
        )
        DesktopIcon.objects.create(
            user=self.user2, tenant=self.tenant2, title='I2',
            content_type=ct, object_id=cat2.id
        )

        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/desktop/', {'parent_id': 'root'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], 'I1')

    def test_sync_settings_update(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/sync/settings/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(SyncPreference.objects.filter(user=self.user, tenant=self.tenant1).exists())

        res = self.client.patch('/api/sync/settings/', {'upload_enabled': True, 'conflict_strategy': 'client_wins'}, format='json')
        self.assertEqual(res.status_code, 200)
        pref = SyncPreference.objects.get(user=self.user, tenant=self.tenant1)
        self.assertTrue(pref.upload_enabled)
        self.assertEqual(pref.conflict_strategy, 'client_wins')

    def test_sync_push_server_wins(self):
        cat = Category.objects.create(name='C1', tenant=self.tenant1)
        ct = ContentType.objects.get_for_model(Category)
        icon = DesktopIcon.objects.create(
            user=self.user, tenant=self.tenant1, title='I1',
            content_type=ct, object_id=cat.id, x=10, y=10
        )
        icon.updated_at = timezone.now()
        icon.save()

        self.client.force_authenticate(user=self.user)
        payload = {
            'conflict_strategy': 'server_wins',
            'icons': [{
                'id': icon.id,
                'x': 100,
                'y': 100,
                'updated_at': (icon.updated_at - timezone.timedelta(days=1)).isoformat()
            }]
        }
        res = self.client.post('/api/sync/push/', payload, format='json')
        self.assertEqual(res.status_code, 200)
        icon.refresh_from_db()
        self.assertEqual(icon.x, 10)
        self.assertEqual(icon.y, 10)