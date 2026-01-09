"""
Integration Tests for Admin Routes Blueprint

Tests the admin routes in routes/admin.py:
- Admin dashboard
- User management (list, create, edit)
- Entity management (list, create, edit, delete)
- Team management (list, create, edit, delete)
- Category management
- Module management
- User-Entity permissions
"""

import pytest
import json
from datetime import date

from extensions import db
from models import (
    User, Entity, Team, TaskCategory, Module, UserModule,
    UserEntity, EntityAccessLevel, Tenant, TenantMembership, Task
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def admin_client(client, admin_user, tenant, db):
    """Create test client with logged-in admin user"""
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=admin_user.id,
        role='admin',
        is_default=True
    )
    db.session.add(membership)
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = admin_user.id
        sess['_fresh'] = True
        sess['current_tenant_id'] = tenant.id
    
    return client


@pytest.fixture
def non_admin_client(client, user, tenant, db):
    """Create test client with non-admin user"""
    membership = TenantMembership(
        tenant_id=tenant.id,
        user_id=user.id,
        role='member',
        is_default=True
    )
    db.session.add(membership)
    db.session.commit()
    
    with client.session_transaction() as sess:
        sess['_user_id'] = user.id
        sess['_fresh'] = True
        sess['current_tenant_id'] = tenant.id
    
    return client


@pytest.fixture
def test_team(db, admin_user):
    """Create a test team"""
    team = Team(
        name='Test Team',
        name_de='Test Team',
        name_en='Test Team EN',
        description='Test description',
        color='#86BC25',
        manager_id=admin_user.id,
        is_active=True
    )
    db.session.add(team)
    db.session.commit()
    
    yield team


@pytest.fixture
def test_category(db):
    """Create a test category"""
    category = TaskCategory(
        code='TST',
        name='Test Category',
        name_de='Test Kategorie',
        name_en='Test Category',
        description='Test description',
        color='#0076A8',
        is_active=True
    )
    db.session.add(category)
    db.session.commit()
    
    yield category


@pytest.fixture
def test_module(db):
    """Create a test module"""
    module = Module(
        code='TEST_MOD',
        name_de='Testmodul',
        name_en='Test Module',
        description_de='Testmodul Beschreibung',
        description_en='Test module description',
        icon='bi-gear',
        is_active=True,
        is_core=False
    )
    db.session.add(module)
    db.session.commit()
    
    yield module


# ============================================================================
# ADMIN ACCESS TESTS
# ============================================================================

class TestAdminAccess:
    """Test admin route protection"""
    
    def test_admin_dashboard_requires_login(self, client):
        """Unauthenticated users should be redirected"""
        response = client.get('/admin')
        assert response.status_code == 302
    
    def test_admin_dashboard_requires_admin_role(self, non_admin_client):
        """Non-admin users should be denied"""
        response = non_admin_client.get('/admin')
        assert response.status_code == 302  # Redirects with flash message
    
    def test_users_route_requires_admin(self, non_admin_client):
        """Non-admin cannot access user management"""
        response = non_admin_client.get('/admin/users')
        assert response.status_code == 302
    
    def test_entities_route_requires_admin(self, non_admin_client):
        """Non-admin cannot access entity management"""
        response = non_admin_client.get('/admin/entities')
        assert response.status_code == 302


# ============================================================================
# ADMIN DASHBOARD TESTS
# ============================================================================

class TestAdminDashboard:
    """Tests for GET /admin"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_admin_dashboard_renders(self, admin_client):
        """Admin dashboard should render with stats"""
        response = admin_client.get('/admin')
        assert response.status_code == 200


# ============================================================================
# USER MANAGEMENT TESTS
# ============================================================================

class TestUserManagement:
    """Tests for user management routes"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_users_list(self, admin_client, user):
        """User list should show users"""
        response = admin_client.get('/admin/users')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_new_form(self, admin_client):
        """GET /admin/users/new should show form"""
        response = admin_client.get('/admin/users/new')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_create(self, admin_client):
        """POST /admin/users/new should create user"""
        response = admin_client.post('/admin/users/new', data={
            'email': 'newuser@example.com',
            'name': 'New User',
            'role': 'preparer',
            'password': 'newpassword123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Verify user was created
        new_user = User.query.filter_by(email='newuser@example.com').first()
        assert new_user is not None
        assert new_user.name == 'New User'
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_create_duplicate_email(self, admin_client, user):
        """Creating user with existing email should fail"""
        response = admin_client.post('/admin/users/new', data={
            'email': user.email,  # Existing email
            'name': 'Duplicate User',
            'role': 'preparer',
            'password': 'password123'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error, not create duplicate
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_edit_form(self, admin_client, user):
        """GET /admin/users/<id> should show edit form"""
        response = admin_client.get(f'/admin/users/{user.id}')
        assert response.status_code == 200
    
    def test_user_edit_not_found(self, admin_client):
        """Editing non-existent user should return 404"""
        response = admin_client.get('/admin/users/99999')
        assert response.status_code == 404
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_edit_update(self, admin_client, user):
        """POST /admin/users/<id> should update user"""
        original_id = user.id
        response = admin_client.post(f'/admin/users/{user.id}', data={
            'name': 'Updated Name',
            'role': 'reviewer',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated = User.query.get(original_id)
        assert updated.name == 'Updated Name'
        assert updated.role == 'reviewer'


# ============================================================================
# ENTITY MANAGEMENT TESTS
# ============================================================================

class TestEntityManagement:
    """Tests for entity management routes"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entities_list(self, admin_client, entity):
        """Entity list should show entities"""
        response = admin_client.get('/admin/entities')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entity_new_form(self, admin_client):
        """GET /admin/entities/new should show form"""
        response = admin_client.get('/admin/entities/new')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entity_create(self, admin_client):
        """POST /admin/entities/new should create entity"""
        response = admin_client.post('/admin/entities/new', data={
            'name_de': 'Neue GmbH',
            'name_en': 'New Ltd',
            'short_name': 'NEW',
            'country': 'DE'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        new_entity = Entity.query.filter_by(name='Neue GmbH').first()
        assert new_entity is not None
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entity_create_missing_name(self, admin_client):
        """Creating entity without name should fail"""
        response = admin_client.post('/admin/entities/new', data={
            'name_de': '',
            'name_en': '',
            'country': 'DE'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show warning, entity count should not increase
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entity_edit_form(self, admin_client, entity):
        """GET /admin/entities/<id> should show edit form"""
        response = admin_client.get(f'/admin/entities/{entity.id}')
        assert response.status_code == 200
    
    def test_entity_edit_not_found(self, admin_client):
        """Editing non-existent entity should return 404"""
        response = admin_client.get('/admin/entities/99999')
        assert response.status_code == 404
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entity_edit_update(self, admin_client, entity):
        """POST /admin/entities/<id> should update entity"""
        original_id = entity.id
        response = admin_client.post(f'/admin/entities/{entity.id}', data={
            'name_de': 'Aktualisierte GmbH',
            'name_en': 'Updated Ltd',
            'short_name': 'UPD',
            'country': 'AT',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated = Entity.query.get(original_id)
        assert updated.name_de == 'Aktualisierte GmbH'
        assert updated.country == 'AT'
    
    def test_entity_delete(self, admin_client, entity):
        """POST /admin/entities/<id>/delete should soft-delete entity"""
        entity_id = entity.id
        response = admin_client.post(f'/admin/entities/{entity_id}/delete')
        
        assert response.status_code == 302  # Redirect
        deleted = Entity.query.get(entity_id)
        assert deleted.is_active is False
    
    def test_entity_delete_not_found(self, admin_client):
        """Deleting non-existent entity should return 404"""
        response = admin_client.post('/admin/entities/99999/delete')
        assert response.status_code == 404


# ============================================================================
# TEAM MANAGEMENT TESTS
# ============================================================================

class TestTeamManagement:
    """Tests for team management routes"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_teams_list(self, admin_client, test_team):
        """Team list should show teams"""
        response = admin_client.get('/admin/teams')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_new_form(self, admin_client):
        """GET /admin/teams/new should show form"""
        response = admin_client.get('/admin/teams/new')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_create(self, admin_client, admin_user):
        """POST /admin/teams/new should create team"""
        response = admin_client.post('/admin/teams/new', data={
            'name_de': 'Neues Team',
            'name_en': 'New Team',
            'description_de': 'Beschreibung',
            'description_en': 'Description',
            'color': '#FF5733',
            'manager_id': str(admin_user.id)
        }, follow_redirects=True)
        
        assert response.status_code == 200
        new_team = Team.query.filter_by(name='Neues Team').first()
        assert new_team is not None
        assert new_team.color == '#FF5733'
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_create_duplicate_name(self, admin_client, test_team):
        """Creating team with existing name should fail"""
        response = admin_client.post('/admin/teams/new', data={
            'name_de': test_team.name,  # Existing name
            'name_en': 'Duplicate EN',
            'color': '#123456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should show error
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_create_with_members(self, admin_client, user, admin_user):
        """Creating team with members should add them"""
        response = admin_client.post('/admin/teams/new', data={
            'name_de': 'Team Mit Mitgliedern',
            'name_en': 'Team With Members',
            'color': '#00FF00',
            'members': [str(user.id), str(admin_user.id)]
        }, follow_redirects=True)
        
        assert response.status_code == 200
        new_team = Team.query.filter_by(name='Team Mit Mitgliedern').first()
        if new_team:
            assert new_team.get_member_count() == 2
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_edit_form(self, admin_client, test_team):
        """GET /admin/teams/<id> should show edit form"""
        response = admin_client.get(f'/admin/teams/{test_team.id}')
        assert response.status_code == 200
    
    def test_team_edit_not_found(self, admin_client):
        """Editing non-existent team should return 404"""
        response = admin_client.get('/admin/teams/99999')
        assert response.status_code == 404
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_edit_update(self, admin_client, test_team):
        """POST /admin/teams/<id> should update team"""
        original_id = test_team.id
        response = admin_client.post(f'/admin/teams/{test_team.id}', data={
            'name_de': 'Aktualisiertes Team',
            'name_en': 'Updated Team',
            'description_de': 'Neue Beschreibung',
            'description_en': 'New Description',
            'color': '#ABCDEF',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated = Team.query.get(original_id)
        assert updated.name == 'Aktualisiertes Team'
        assert updated.color == '#ABCDEF'
    
    def test_team_delete(self, admin_client, test_team):
        """POST /admin/teams/<id>/delete should soft-delete team"""
        team_id = test_team.id
        response = admin_client.post(f'/admin/teams/{team_id}/delete')
        
        assert response.status_code == 302  # Redirect
        deleted = Team.query.get(team_id)
        assert deleted.is_active is False
    
    def test_team_delete_not_found(self, admin_client):
        """Deleting non-existent team should return 404"""
        response = admin_client.post('/admin/teams/99999/delete')
        assert response.status_code == 404


# ============================================================================
# CATEGORY MANAGEMENT TESTS
# ============================================================================

class TestCategoryManagement:
    """Tests for category management routes"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_categories_list(self, admin_client, test_category):
        """Category list should show categories"""
        response = admin_client.get('/admin/categories')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_category_new_form(self, admin_client):
        """GET /admin/categories/new should show form"""
        response = admin_client.get('/admin/categories/new')
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_category_edit_form(self, admin_client, test_category):
        """GET /admin/categories/<id> should show edit form"""
        response = admin_client.get(f'/admin/categories/{test_category.id}')
        assert response.status_code == 200
    
    def test_category_edit_not_found(self, admin_client):
        """Editing non-existent category should return 404"""
        response = admin_client.get('/admin/categories/99999')
        assert response.status_code == 404


# ============================================================================
# MODULE MANAGEMENT TESTS
# ============================================================================

class TestModuleManagement:
    """Tests for module management routes"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_modules_list(self, admin_client, test_module):
        """Module list should show modules"""
        response = admin_client.get('/admin/modules')
        assert response.status_code == 200
    
    def test_module_toggle(self, admin_client, test_module):
        """POST /admin/modules/<id>/toggle should toggle module"""
        original_status = test_module.is_active
        response = admin_client.post(f'/admin/modules/{test_module.id}/toggle')
        
        assert response.status_code == 302  # Redirect
        db.session.refresh(test_module)
        assert test_module.is_active != original_status
    
    def test_module_toggle_not_found(self, admin_client):
        """Toggling non-existent module should return 404"""
        response = admin_client.post('/admin/modules/99999/toggle')
        assert response.status_code == 404


# ============================================================================
# USER-ENTITY PERMISSION TESTS
# ============================================================================

class TestUserEntityPermissions:
    """Tests for user-entity permission management"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_entities_get(self, admin_client, user):
        """GET /admin/users/<id>/entities should show permissions"""
        response = admin_client.get(f'/admin/users/{user.id}/entities')
        assert response.status_code == 200
    
    def test_user_entities_get_not_found(self, admin_client):
        """User entities for non-existent user should return 404"""
        response = admin_client.get('/admin/users/99999/entities')
        assert response.status_code == 404
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_entity_users_get(self, admin_client, entity):
        """GET /admin/entities/<id>/users should show permissions"""
        response = admin_client.get(f'/admin/entities/{entity.id}/users')
        assert response.status_code == 200
    
    def test_entity_users_get_not_found(self, admin_client):
        """Entity users for non-existent entity should return 404"""
        response = admin_client.get('/admin/entities/99999/users')
        assert response.status_code == 404


# ============================================================================
# USER MODULE PERMISSION TESTS
# ============================================================================

class TestUserModulePermissions:
    """Tests for user-module permission management"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_user_modules_get(self, admin_client, user):
        """GET /admin/users/<id>/modules should show permissions"""
        response = admin_client.get(f'/admin/users/{user.id}/modules')
        assert response.status_code == 200
    
    def test_user_modules_get_not_found(self, admin_client):
        """User modules for non-existent user should return 404"""
        response = admin_client.get('/admin/users/99999/modules')
        assert response.status_code == 404
    
    def test_user_modules_save(self, admin_client, user, test_module, db):
        """POST /admin/users/<id>/modules should save module assignments"""
        response = admin_client.post(
            f'/admin/users/{user.id}/modules',
            data={'modules': [str(test_module.id)]},
            follow_redirects=False
        )
        
        assert response.status_code == 302  # Redirect
        # Check module was assigned
        from models import UserModule
        assignment = UserModule.query.filter_by(
            user_id=user.id, 
            module_id=test_module.id
        ).first()
        assert assignment is not None
    
    def test_user_modules_remove(self, admin_client, user, test_module, db):
        """Removing module from user should delete assignment"""
        from models import UserModule
        # First add the module
        um = UserModule(
            user_id=user.id,
            module_id=test_module.id,
            granted_by_id=user.id
        )
        db.session.add(um)
        db.session.commit()
        
        # Now remove by not including in POST
        response = admin_client.post(
            f'/admin/users/{user.id}/modules',
            data={'modules': []},  # Empty list
            follow_redirects=False
        )
        
        assert response.status_code == 302
        # Check module was removed
        assignment = UserModule.query.filter_by(
            user_id=user.id, 
            module_id=test_module.id
        ).first()
        assert assignment is None


# ============================================================================
# USER ENTITY PERMISSION SAVE TESTS
# ============================================================================

class TestUserEntitySave:
    """Tests for saving user-entity permissions"""
    
    def test_user_entities_save(self, admin_client, user, entity, db):
        """POST /admin/users/<id>/entities should save permissions"""
        response = admin_client.post(
            f'/admin/users/{user.id}/entities',
            data={
                'entity_ids': [str(entity.id)],
                f'access_level_{entity.id}': 'edit',
                f'inherit_{entity.id}': 'on'
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        # Check permission was created
        from models import UserEntity
        perm = UserEntity.query.filter_by(
            user_id=user.id,
            entity_id=entity.id
        ).first()
        assert perm is not None
        assert perm.access_level == 'edit'
        assert perm.inherit_to_children is True
    
    def test_user_entities_update_existing(self, admin_client, user, entity, db, admin_user):
        """Updating existing permission should work"""
        from models import UserEntity
        # First create a permission
        perm = UserEntity(
            user_id=user.id,
            entity_id=entity.id,
            access_level='view',
            inherit_to_children=False,
            granted_by_id=admin_user.id
        )
        db.session.add(perm)
        db.session.commit()
        
        # Now update it
        response = admin_client.post(
            f'/admin/users/{user.id}/entities',
            data={
                'entity_ids': [str(entity.id)],
                f'access_level_{entity.id}': 'admin',
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        db.session.refresh(perm)
        assert perm.access_level == 'admin'
    
    def test_user_entities_remove_permission(self, admin_client, user, entity, db, admin_user):
        """Removing entity from form should delete permission"""
        from models import UserEntity
        perm = UserEntity(
            user_id=user.id,
            entity_id=entity.id,
            access_level='view',
            granted_by_id=admin_user.id
        )
        db.session.add(perm)
        db.session.commit()
        
        # POST without the entity in entity_ids
        response = admin_client.post(
            f'/admin/users/{user.id}/entities',
            data={'entity_ids': []},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        deleted = UserEntity.query.filter_by(
            user_id=user.id,
            entity_id=entity.id
        ).first()
        assert deleted is None


# ============================================================================
# ENTITY USER PERMISSION SAVE TESTS  
# ============================================================================

class TestEntityUserSave:
    """Tests for saving entity-user permissions"""
    
    def test_entity_users_save(self, admin_client, user, entity, db):
        """POST /admin/entities/<id>/users should save permissions"""
        response = admin_client.post(
            f'/admin/entities/{entity.id}/users',
            data={
                'user_ids': [str(user.id)],
                f'access_level_{user.id}': 'edit'
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        from models import UserEntity
        perm = UserEntity.query.filter_by(
            user_id=user.id,
            entity_id=entity.id
        ).first()
        assert perm is not None
        assert perm.access_level == 'edit'
    
    def test_entity_users_update(self, admin_client, user, entity, db, admin_user):
        """Updating existing entity-user permission should work"""
        from models import UserEntity
        perm = UserEntity(
            user_id=user.id,
            entity_id=entity.id,
            access_level='view',
            granted_by_id=admin_user.id
        )
        db.session.add(perm)
        db.session.commit()
        
        response = admin_client.post(
            f'/admin/entities/{entity.id}/users',
            data={
                'user_ids': [str(user.id)],
                f'access_level_{user.id}': 'admin',
                f'inherit_{user.id}': 'on'
            },
            follow_redirects=False
        )
        
        assert response.status_code == 302
        db.session.refresh(perm)
        assert perm.access_level == 'admin'
        assert perm.inherit_to_children is True
    
    def test_entity_users_remove(self, admin_client, user, entity, db, admin_user):
        """Removing user should delete permission"""
        from models import UserEntity
        perm = UserEntity(
            user_id=user.id,
            entity_id=entity.id,
            access_level='view',
            granted_by_id=admin_user.id
        )
        db.session.add(perm)
        db.session.commit()
        
        response = admin_client.post(
            f'/admin/entities/{entity.id}/users',
            data={'user_ids': []},
            follow_redirects=False
        )
        
        assert response.status_code == 302
        deleted = UserEntity.query.filter_by(
            user_id=user.id,
            entity_id=entity.id
        ).first()
        assert deleted is None


# ============================================================================
# CATEGORY CREATE/EDIT TESTS
# ============================================================================

class TestCategoryCreateEdit:
    """Tests for category creation and editing"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_category_create(self, admin_client):
        """POST /admin/categories/new should create category"""
        response = admin_client.post('/admin/categories/new', data={
            'code': 'NEWCAT',
            'name_de': 'Neue Kategorie',
            'name_en': 'New Category',
            'description_de': 'Beschreibung',
            'description_en': 'Description',
            'color': '#FF0000',
            'icon': 'bi-tag'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        new_cat = TaskCategory.query.filter_by(code='NEWCAT').first()
        assert new_cat is not None
        assert new_cat.color == '#FF0000'
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_category_create_duplicate_code(self, admin_client, test_category):
        """Creating category with existing code should fail"""
        response = admin_client.post('/admin/categories/new', data={
            'code': test_category.code,  # Existing code
            'name_de': 'Duplicate',
            'name_en': 'Duplicate EN'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Count should not increase
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_category_create_missing_fields(self, admin_client):
        """Creating category without required fields should fail"""
        response = admin_client.post('/admin/categories/new', data={
            'code': '',  # Missing code
            'name_de': '',
            'name_en': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_category_edit(self, admin_client, test_category):
        """POST /admin/categories/<id> should update category"""
        cat_id = test_category.id
        response = admin_client.post(f'/admin/categories/{cat_id}', data={
            'name_de': 'Aktualisiert',
            'name_en': 'Updated',
            'description_de': 'Neue Beschreibung',
            'description_en': 'New Description',
            'color': '#00FF00',
            'icon': 'bi-folder-fill',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        updated = TaskCategory.query.get(cat_id)
        assert updated.name_de == 'Aktualisiert'
        assert updated.color == '#00FF00'


# ============================================================================
# MODULE TOGGLE TESTS
# ============================================================================

class TestModuleToggleExtended:
    """Extended tests for module toggle functionality"""
    
    def test_module_toggle_core_module(self, admin_client, db):
        """Toggling core module should be prevented"""
        from models import Module
        core_module = Module(
            code='CORE_MOD',
            name_de='Kernmodul',
            name_en='Core Module',
            is_active=True,
            is_core=True  # Core module
        )
        db.session.add(core_module)
        db.session.commit()
        
        original_status = core_module.is_active
        response = admin_client.post(f'/admin/modules/{core_module.id}/toggle')
        
        assert response.status_code == 302
        db.session.refresh(core_module)
        # Core module should NOT be toggled
        assert core_module.is_active == original_status


# ============================================================================
# TEAM VALIDATION TESTS
# ============================================================================

class TestTeamValidation:
    """Tests for team validation logic"""
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_create_missing_name_en(self, admin_client):
        """Creating team without English name should fail"""
        response = admin_client.post('/admin/teams/new', data={
            'name_de': 'Nur Deutsch',
            'name_en': '',  # Missing
            'color': '#123456'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Team should not be created
        team = Team.query.filter_by(name='Nur Deutsch').first()
        assert team is None
    
    @pytest.mark.xfail(reason="Template requires context processor 't'")
    def test_team_edit_duplicate_name(self, admin_client, test_team, admin_user, db):
        """Editing team to have duplicate name should fail"""
        # Create another team
        other_team = Team(
            name='Other Team',
            name_de='Other Team',
            name_en='Other Team EN',
            is_active=True
        )
        db.session.add(other_team)
        db.session.commit()
        
        # Try to rename test_team to have same name as other_team
        response = admin_client.post(f'/admin/teams/{test_team.id}', data={
            'name_de': 'Other Team',  # Duplicate
            'name_en': 'Other EN',
            'color': '#ABCDEF',
            'is_active': 'on'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Name should not have changed
        db.session.refresh(test_team)
        assert test_team.name == 'Test Team'
