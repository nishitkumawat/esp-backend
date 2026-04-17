from django.db import models
from django.utils import timezone
import uuid
import os

def invoice_pdf_path(instance, filename):
    """Generate path for storing invoice PDF files"""
    return f'invoices/{instance.invoice_no}/{filename}'

class Invoice(models.Model):
    """Invoice model for storing customer invoice information"""
    
    PAYMENT_METHODS = [
        ('UPI', 'UPI'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
    ]
    
    WHATSAPP_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    # Auto-generated fields
    invoice_no = models.CharField(max_length=20, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Customer Information
    customer_name = models.CharField(max_length=200)
    customer_address = models.TextField()
    phone = models.CharField(max_length=10, help_text="Customer phone number")
    
    # Product Information
    product_name = models.CharField(max_length=200, default="Solar Wash Controller")
    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    # Payment and Shipping
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    shipment_details = models.TextField(blank=True, null=True)
    
    # Additional Fields
    notes = models.TextField(blank=True, null=True)
    
    # WhatsApp tracking only
    whatsapp_status = models.CharField(max_length=20, choices=WHATSAPP_STATUS_CHOICES, default='PENDING')
    whatsapp_sent_at = models.DateTimeField(blank=True, null=True)
    whatsapp_error = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"
    
    def __str__(self):
        return f"Invoice #{self.invoice_no} - {self.customer_name}"
    
    def save(self, *args, **kwargs):
        # Generate invoice number if not exists
        if not self.invoice_no:
            self.invoice_no = self.generate_invoice_no()
        
        # Calculate total amount
        self.total_amount = self.quantity * self.price_per_unit
        
        super().save(*args, **kwargs)
    
    def generate_invoice_no(self):
        """Generate unique invoice number with format: INV-YYYYMMDD-XXXX"""
        today = timezone.now().strftime('%Y%m%d')
        last_invoice = Invoice.objects.filter(invoice_no__startswith=f'INV-{today}').order_by('invoice_no').last()
        
        if last_invoice:
            last_seq = int(last_invoice.invoice_no.split('-')[-1])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f'INV-{today}-{new_seq:04d}'
    
    @property
    def invoice_date(self):
        """Get invoice creation date formatted"""
        return self.created_at.strftime('%d/%m/%Y')
    
    @property
    def formatted_total(self):
        """Get formatted total amount with currency symbol"""
        return f"₹{self.total_amount:,.2f}"
    
    @property
    def whatsapp_status_display(self):
        """Get display text for WhatsApp status"""
        return dict(self.WHATSAPP_STATUS_CHOICES).get(self.whatsapp_status, self.whatsapp_status)
