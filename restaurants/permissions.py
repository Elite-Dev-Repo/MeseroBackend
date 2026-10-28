from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.owner


class IsOwnerOrStaffOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        is_owner = request.user == obj.owner
        is_active_staff = obj.staff_for_restaurant.filter(user=request.user, is_active=True).exists()
        return is_owner or is_active_staff

