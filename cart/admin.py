# REPLACE the existing cart/admin.py with this:

from django.contrib import admin
from .models import Order, Item, CustomerFeedback

class CustomerFeedbackAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'order', 'created_at', 'feedback_preview']
    list_filter = ['created_at']
    search_fields = ['name', 'feedback_text', 'order__id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def feedback_preview(self, obj):
        return obj.feedback_text[:50] + "..." if len(obj.feedback_text) > 50 else obj.feedback_text
    feedback_preview.short_description = "Feedback Preview"

admin.site.register(Order)
admin.site.register(Item)
admin.site.register(CustomerFeedback, CustomerFeedbackAdmin)