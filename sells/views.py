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
from .utils.db_logger import DatabaseLogHandler

# Configure logger with database handler
logger = logging.getLogger(__name__)
logger.addHandler(DatabaseLogHandler())

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
                logger.error(f"PDF generation failed: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
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
                logger.error(f"WhatsApp sending failed: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            invoice.save()
            
            logger.info(f"Invoice creation completed successfully")
            
            return JsonResponse({
                'success': True,
                'invoice_no': invoice.invoice_no,
                'message': 'Invoice created successfully!'
            })
            
        except Exception as e:
            logger.error(f"Unexpected error in invoice creation: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
            logger.error(f"Error rendering invoice creation form: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
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
        logger.error(f"Error loading invoice list: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        logger.error(f"Error viewing invoice {invoice_no}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        logger.error(f"Error generating PDF for invoice {invoice_no}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        logger.error(f"Error deleting invoice {invoice_id}: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while deleting the invoice.'
        })




def generate_invoice_pdf(invoice):
    """Generate PDF invoice using WeasyPrint"""
    from django.conf import settings
    from pathlib import Path
    import urllib.parse
    import tempfile
    import shutil
    
    # Create temporary directory for PDF
    temp_dir = tempfile.mkdtemp(prefix=f'invoice_{invoice.invoice_no}_')
    
    # Pass absolute logo path
    logo_path = os.path.join(settings.BASE_DIR, 'logo_without_bg.PNG')
    logo_uri = Path(logo_path).as_uri() if os.path.exists(logo_path) else ''
    
    # Generate HTML content
    html_content = render_to_string('sells/invoice_pdf.html', {
        'invoice': invoice,
        'logo_uri': logo_uri
    })
    
    # Generate PDF
    # Base URL allows resolving any local paths if needed
    html = HTML(string=html_content, base_url=Path(settings.BASE_DIR).as_uri())
    
    pdf_path = os.path.join(temp_dir, f'Invoice_{invoice.invoice_no}.pdf')
    html.write_pdf(pdf_path)
    
    # Schedule deletion after 1 hour (3600 seconds)
    import threading
    import time
    
    def delete_temp_files():
        time.sleep(3600)  # Wait 1 hour
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"DEBUG: Temporary PDF files deleted for invoice {invoice.invoice_no}")
        except Exception as e:
            print(f"DEBUG: Error deleting temp files: {e}")
    
    # Start deletion in background thread
    deletion_thread = threading.Thread(target=delete_temp_files, daemon=True)
    deletion_thread.start()
    
    return pdf_path

def send_whatsapp_invoice(invoice, pdf_path=None):
    """Send invoice PDF via WhatsApp bot running on VPS"""
    WHATSAPP_BOT_URL = "http://203.174.22.81:3001/send-document"
    
    # Prepare message
    message = f"""Hello {invoice.customer_name},

Thank you for choosing EZrun Automation.

Your invoice #{invoice.invoice_no} has been generated successfully.

Invoice Details:
• Customer: {invoice.customer_name}
• Product: {invoice.product_name}
• Quantity: {invoice.quantity}
• Price per unit: ₹{invoice.price_per_unit}
• Total amount: ₹{invoice.total_amount}

Payment Method: {invoice.get_payment_method_display()}

Your invoice PDF is attached to this message.

Best regards,
EZrun Automation Team
www.ezrun.in | +91 99744 86076"""
    
    try:
        # Check if PDF exists
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path, 'rb') as pdf_file:
                files = {
                    'document': (f'Invoice_{invoice.invoice_no}.pdf', pdf_file, 'application/pdf')
                }
                
                payload = {
                    'phone': "91"+invoice.phone,
                    'message': message,
                    'filename': f'Invoice_{invoice.invoice_no}.pdf'
                }
                
                response = requests.post(
                    WHATSAPP_BOT_URL,
                    files=files,
                    data=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print(f"WhatsApp sent successfully to {invoice.phone}")
                else:
                    print(f"WhatsApp failed with status code: {response.status_code}")
                    print(f"Response: {response.text}")
        else:
            print(f"PDF file not found at: {pdf_path}")
            
    except Exception as e:
        print(f"Error sending WhatsApp: {str(e)}")
        raise

