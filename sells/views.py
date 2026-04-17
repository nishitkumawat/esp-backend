import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone
import json
import os
import traceback
from weasyprint import HTML, CSS
import requests
from .models import Invoice

# Configure logger
logger = logging.getLogger(__name__)

# Create your views here.

def invoice_create(request):
    """Create a new invoice"""
    logger.info(f"Request method: {request.method}")
    
    if request.method == 'POST':
        logger.info(f"Processing POST request")
        logger.debug(f"POST data keys: {list(request.POST.keys())}")
        logger.debug(f"POST data items: {list(request.POST.items())}")
        
        try:
            # Get form data manually
            customer_name = request.POST.get('customer_name', '')
            customer_address = request.POST.get('customer_address', '')
            phone = request.POST.get('phone', '')
            product_name = request.POST.get('product_name', '')
            
            logger.info(f"Form data received - product_name: {product_name}")
            logger.debug(f"All POST data: {dict(request.POST)}")
            
            # Validate product selection
            if product_name not in ['Solar Wash Controller', 'Shutter Controller']:
                return JsonResponse({
                    'success': False,
                    'errors': {'product_name': 'Please select a valid product'}
                })
            quantity = request.POST.get('quantity', '1')
            price_per_unit = request.POST.get('price_per_unit', '0')
            payment_method = request.POST.get('payment_method', '')
            shipment_details = request.POST.get('shipment_details', '')
            notes = request.POST.get('notes', '')
            
            # Validate required fields
            errors = {}
            if not customer_name:
                errors['customer_name'] = 'Customer name is required'
            if not customer_address:
                errors['customer_address'] = 'Customer address is required'
            if not phone:
                errors['phone'] = 'Phone number is required'
            if not product_name:
                errors['product_name'] = 'Product selection is required'
            if not payment_method:
                errors['payment_method'] = 'Payment method is required'
            
            if errors:
                logger.warning(f"Validation errors: {errors}")
                return JsonResponse({
                    'success': False,
                    'errors': errors
                })
            
            logger.info(f"Creating invoice with data: {customer_name}, {product_name}")
            
            # Create invoice
            invoice = Invoice.objects.create(
                customer_name=customer_name,
                customer_address=customer_address,
                phone=phone,
                product_name=product_name,
                quantity=int(quantity) if quantity else 1,
                price_per_unit=float(price_per_unit) if price_per_unit else 0,
                payment_method=payment_method,
                shipment_details=shipment_details,
                notes=notes
            )
            
            logger.info(f"Invoice created with ID: {invoice.id}, Invoice No: {invoice.invoice_no}")
            
            # Generate PDF on-demand only
            pdf_path = None
            try:
                pdf_path = generate_invoice_pdf(invoice)
                logger.info(f"PDF generated temporarily at {pdf_path}")
            except Exception as e:
                logger.exception(f"PDF generation failed: {e}")
                logger.exception(f"Traceback: {traceback.format_exc()}")
                # Continue without PDF for now
                pdf_path = None
            
            # Send WhatsApp message
            try:
                send_whatsapp_invoice(invoice, pdf_path)
                invoice.whatsapp_status = 'SENT'
                invoice.whatsapp_sent_at = timezone.now()
                logger.info(f"WhatsApp sent successfully to {invoice.phone}")
            except Exception as e:
                invoice.whatsapp_status = 'FAILED'
                invoice.whatsapp_error = str(e)
                logger.exception(f"WhatsApp sending failed: {e}")
                logger.exception(f"Traceback: {traceback.format_exc()}")
            
            invoice.save()
            
            logger.info(f"Invoice creation completed successfully")
            
            return JsonResponse({
                'success': True,
                'invoice_no': invoice.invoice_no,
                'message': 'Invoice created successfully!'
            })
            
        except Exception as e:
            logger.exception(f"Unexpected error in invoice creation: {e}")
            logger.exception(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': 'An unexpected error occurred. Please try again.'
            })
    
    else:
        # GET request - display form
        try:
            # Get next invoice number for display
            last_invoice = Invoice.objects.all().order_by('-created_at').first()
            if last_invoice and last_invoice.invoice_no:
                try:
                    last_seq = int(last_invoice.invoice_no.split('-')[-1])
                except (ValueError, IndexError):
                    last_seq = 0
            else:
                last_seq = 0
            next_seq = last_seq + 1
            next_invoice_no = f"INV-{timezone.now().strftime('%Y%m%d')}-{next_seq:04d}"
            
            context = {
                'next_invoice_no': next_invoice_no,
                'products': [
                    ('Solar Wash Controller', 'Solar Wash Controller'),
                    ('Shutter Controller', 'Shutter Controller')
                ]
            }
            
            return render(request, 'sells/invoice_create.html', context)
            
        except Exception as e:
            logger.exception(f"Error rendering invoice creation form: {e}")
            logger.exception(f"Traceback: {traceback.format_exc()}")
            return render(request, 'sells/invoice_create.html', {
                'error': 'An error occurred while loading the form.'
            })
    
    # Get next invoice number for display
    last_invoice = Invoice.objects.all().order_by('-created_at').first()
    if last_invoice and last_invoice.invoice_no:
        try:
            last_seq = int(last_invoice.invoice_no.split('-')[-1])
        except (ValueError, IndexError):
            last_seq = 0
    else:
        last_seq = 0
    next_seq = last_seq + 1
    next_invoice_no = f"INV-{timezone.now().strftime('%Y%m%d')}-{next_seq:04d}"
    
    context = {
        'next_invoice_no': next_invoice_no,
        'products': [
            ('Solar Wash Controller', 'Solar Wash Controller'),
            ('Shutter Controller', 'Shutter Controller')
        ]
    }
    
    return render(request, 'sells/invoice_create.html', context)

def invoice_list(request):
    """List all invoices with search functionality"""
    search_query = request.GET.get('search', '')
    
    try:
        invoices = Invoice.objects.all()
        
        if search_query:
            invoices = invoices.filter(
                Q(customer_name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(invoice_no__icontains=search_query)
            )
        
        logger.info(f"Found {invoices.count()} invoices matching search: '{search_query}'")
        
        return render(request, 'sells/invoice_list.html', {
            'invoices': invoices,
            'search_query': search_query
        })
        
    except Exception as e:
        logger.exception(f"Error loading invoice list: {e}")
        logger.exception(f"Traceback: {traceback.format_exc()}")
        return render(request, 'sells/invoice_list.html', {
            'error': 'An error occurred while loading invoices.'
        })

def invoice_view(request, invoice_no):
    """View invoice details"""
    try:
        invoice = get_object_or_404(Invoice, invoice_no=invoice_no)
        logger.info(f"Viewing invoice: {invoice_no}")
        return render(request, 'sells/invoice_view.html', {'invoice': invoice})
    except Exception as e:
        logger.exception(f"Error viewing invoice {invoice_no}: {e}")
        logger.exception(f"Traceback: {traceback.format_exc()}")
        return render(request, 'sells/invoice_view.html', {
            'error': 'An error occurred while loading the invoice.'
        })

def invoice_pdf(request, invoice_no):
    """Generate and serve invoice PDF"""
    try:
        invoice = get_object_or_404(Invoice, invoice_no=invoice_no)
        logger.info(f"Generating PDF for invoice: {invoice_no}")
        
        # Generate PDF on-demand
        pdf_path = generate_invoice_pdf(invoice)
        logger.info(f"PDF generated for viewing at {pdf_path}")
        
        # Serve PDF
        with open(pdf_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="Invoice_{invoice.invoice_no}.pdf"'
            return response
    except Exception as e:
        logger.exception(f"Error generating PDF for invoice {invoice_no}: {e}")
        logger.exception(f"Traceback: {traceback.format_exc()}")
        return HttpResponse("PDF generation failed", status=500)

def invoice_delete(request, invoice_id):
    """Delete an invoice"""
    try:
        if request.method == 'POST':
            invoice = get_object_or_404(Invoice, id=invoice_id)
            logger.info(f"Deleting invoice: {invoice_id}")
            
            # Delete PDF file if exists
            if hasattr(invoice, 'pdf_path') and invoice.pdf_path and os.path.exists(invoice.pdf_path):
                os.remove(invoice.pdf_path)
                logger.info(f"Deleted PDF file: {invoice.pdf_path}")
            
            invoice.delete()
            logger.info(f"Successfully deleted invoice: {invoice_id}")
            
            return JsonResponse({
                'success': True,
                'message': 'Invoice deleted successfully!'
            })
        else:
            logger.warning(f"Invalid request method for invoice deletion: {request.method}")
            return JsonResponse({
                'success': False,
                'message': 'Invalid request method'
            })
    except Exception as e:
        logger.exception(f"Error deleting invoice {invoice_id}: {e}")
        logger.exception(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while deleting the invoice.'
        })


def generate_invoice_pdf(invoice):
    """Generate PDF invoice using WeasyPrint"""
    from django.conf import settings
