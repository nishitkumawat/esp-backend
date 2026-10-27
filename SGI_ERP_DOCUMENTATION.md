# SGI ERP System Documentation

**Version:** 1.0  
**Date:** October 2026  
**Author:** SGI Development Team

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Overview](#2-system-overview)
3. [Technology Stack](#3-technology-stack)
4. [Architecture](#4-architecture)
5. [Installation & Setup](#5-installation--setup)
6. [Features & Modules](#6-features--modules)
7. [User Guide](#7-user-guide)
8. [Workflow Processes](#8-workflow-processes)
9. [Database Schema](#9-database-schema)
10. [API Documentation](#10-api-documentation)
11. [Security](#11-security)
12. [Performance Optimization](#12-performance-optimization)
13. [Troubleshooting](#13-troubleshooting)
14. [Maintenance](#14-maintenance)
15. [Future Enhancements](#15-future-enhancements)
16. [Appendices](#16-appendices)

---

## 1. Introduction

### 1.1 Purpose

The SGI ERP (Enterprise Resource Planning) system is a comprehensive inventory and manufacturing management solution designed to streamline operations for manufacturing businesses. This system provides real-time tracking of inventory, manufacturing processes, stock movements, dispatch operations, and comprehensive audit trails.

### 1.2 Scope

This documentation covers the complete SGI ERP system including:
- Inventory management
- Manufacturing process tracking
- Stock movement and allocation
- Dispatch and delivery management
- User authentication and authorization
- Reporting and analytics
- System administration

### 1.3 Target Audience

This document is intended for:
- System administrators
- Developers
- Business users
- Operations managers
- IT support staff

### 1.4 Document Conventions

- **Bold text** represents UI elements or important terms
- *Italic text* represents emphasis
- `Code` represents code snippets or commands
- > Block quotes represent notes or warnings

---

## 2. System Overview

### 2.1 System Description

SGI ERP is a web-based inventory and manufacturing management system built on Django framework. It provides a centralized platform for managing all aspects of inventory operations from raw material procurement to finished goods dispatch.

### 2.2 Key Capabilities

- **Real-time Inventory Tracking**: Monitor stock levels across multiple manufacturing processes
- **Process Management**: Define and track manufacturing workflows
- **Stock Allocation**: Assign stock to specific assignees and processes
- **Dispatch Management**: Create and track customer deliveries
- **Audit Trails**: Complete history of all stock movements and operations
- **User Management**: Role-based access control with admin and operator roles
- **Reporting**: Comprehensive dashboards and activity logs

### 2.3 Business Benefits

- Reduced inventory errors through systematic tracking
- Improved visibility into manufacturing processes
- Enhanced accountability with performed-by tracking
- Streamlined dispatch operations with challan generation
- Mobile-responsive interface for on-the-go access
- Optimized database performance for quick operations

### 2.4 System Requirements

**Hardware Requirements:**
- Minimum 4GB RAM
- 20GB available disk space
- Modern processor (Intel i5 or equivalent)

**Software Requirements:**
- Python 3.11.9 or higher
- Django 5.0.2
- MySQL 5.7 or higher
- Modern web browser (Chrome, Firefox, Edge, Safari)

---

## 3. Technology Stack

### 3.1 Backend Technologies

#### 3.1.1 Django Framework
- **Version:** 5.0.2
- **Purpose:** Web framework providing ORM, authentication, and MVC architecture
- **Key Features:**
  - Built-in ORM for database operations
  - Admin interface for quick data management
  - Secure authentication system
  - Template engine for dynamic HTML generation

#### 3.1.2 Python
- **Version:** 3.11.9
- **Purpose:** Primary programming language
- **Key Libraries:**
  - Django ORM
  - Django Authentication
  - Dateutil for date handling
  - Cloudinary for media storage

#### 3.1.3 Database
- **Type:** MySQL
- **Purpose:** Relational data storage
- **Key Features:**
  - ACID compliance for transaction integrity
  - Foreign key relationships for data consistency
  - Indexing for query optimization
  - Full-text search capabilities

### 3.2 Frontend Technologies

#### 3.2.1 HTML5 & CSS3
- **Purpose:** Structure and styling
- **Key Features:**
  - Semantic HTML for accessibility
  - CSS Grid and Flexbox for responsive layouts
  - Custom CSS variables for theming
  - Mobile-first responsive design

#### 3.2.2 Bootstrap Icons
- **Purpose:** Icon library
- **Usage:** Visual indicators throughout the interface
- **Integration:** CDN-based loading

#### 3.2.3 JavaScript
- **Purpose:** Client-side interactivity
- **Usage:** Form validation, dynamic UI updates
- **Framework:** Vanilla JavaScript (no external frameworks)

### 3.3 Third-Party Services

#### 3.3.1 Cloudinary
- **Purpose:** Cloud media storage
- **Usage:** Storing uploaded files and images
- **Benefits:** CDN delivery, automatic optimization

#### 3.3.2 Time Zone Support
- **Library:** pytz
- **Purpose:** Time zone handling
- **Default:** Asia/Kolkata (IST)

### 3.4 Development Tools

#### 3.4.1 Version Control
- **System:** Git
- **Repository:** GitHub
- **Branching Strategy:** Main branch for production

#### 3.4.2 Package Management
- **Tool:** pip
- **File:** requirements.txt
- **Environment:** Virtual environment recommended

---

## 4. Architecture

### 4.1 System Architecture

The SGI ERP follows a Model-View-Controller (MVC) architecture pattern provided by Django:

```
┌─────────────────────────────────────────────────┐
│                   Browser                        │
│              (HTML/CSS/JavaScript)              │
└─────────────────────┬───────────────────────────┘
                      │ HTTP/HTTPS
                      ▼
┌─────────────────────────────────────────────────┐
│              Django Views (Controller)            │
│  - Request handling                             │
│  - Business logic                              │
│  - Response generation                          │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│              Django Models (Model)               │
│  - Data structure                              │
│  - Database operations                         │
│  - Business rules                              │
└─────────────────────┬───────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────┐
│                  MySQL Database                   │
│  - Persistent storage                           │
│  - Query optimization                           │
│  - Data integrity                               │
└─────────────────────────────────────────────────┘
```

### 4.2 Directory Structure

```
backend/
├── SGIERP/                    # Main ERP application
│   ├── __init__.py
│   ├── admin.py              # Django admin configuration
│   ├── apps.py               # Application configuration
│   ├── context_processors.py # Global context data
│   ├── decorators.py         # Custom authentication decorators
│   ├── forms.py              # Django form definitions
│   ├── management/          # Custom management commands
│   │   ├── __init__.py
│   │   └── commands/
│   │       └── reset_erp.py  # Database reset command
│   ├── middleware.py        # Custom middleware
│   ├── migrations/           # Database migrations
│   ├── models.py             # Database models
│   ├── static/               # Static files
│   │   └── sgierp/
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           └── sgi.js
│   ├── templates/            # HTML templates
│   │   └── sgierp/
│   │       ├── auth/         # Authentication templates
│   │       ├── base.html     # Base template
│   │       ├── dashboard/    # Dashboard templates
│   │       ├── dispatch/     # Dispatch templates
│   │       ├── error.html    # Error page
│   │       ├── inventory/    # Inventory templates
│   │       ├── machines/     # Machine templates
│   │       ├── settings/     # Settings templates
│   │       └── challan/      # Challan templates
│   ├── urls.py               # URL routing
│   └── views/                # View functions
│       ├── __init__.py
│       ├── auth.py           # Authentication views
│       ├── challan.py        # Challan views
│       ├── common.py         # Common views
│       ├── dashboard.py      # Dashboard views
│       ├── dispatch.py       # Dispatch views
│       └── inventory.py      # Inventory views
├── backend/                 # Django project settings
│   ├── __init__.py
│   ├── asgi.py              # ASGI configuration
│   ├── settings.py          # Project settings
│   ├── urls.py              # Root URL configuration
│   └── wsgi.py              # WSGI configuration
├── manage.py                # Django management script
└── requirements.txt         # Python dependencies
```

### 4.3 Database Schema

The database consists of the following core models:

1. **ERPUserProfile**: Extended user profile with role information
2. **Item**: Product items with code, name, category, unit
3. **Process**: Manufacturing processes with order and type
4. **ItemProcess**: Junction table linking items to processes
5. **Assignee**: Workers/staff who can be assigned stock
6. **StockHistory**: Audit trail of all stock movements
7. **Machine**: Manufacturing machines with capacity
8. **MachineDispatch**: Dispatch records linked to machines
9. **Challan**: Delivery challan documents
10. **ChallanItem**: Items within a challan

### 4.4 Data Flow

#### 4.4.1 Stock Addition Flow

```
User → Add Stock Form → Validation → Create ItemProcess Entry
                                     ↓
                               Create StockHistory
                                     ↓
                               Update Dashboard Stats
```

#### 4.4.2 Stock Movement Flow

```
User → Move Stock Form → Validation → Convert Stock
                                     ↓
                               Create New ItemProcess Entry
                                     ↓
                               Create StockHistory
                                     ↓
                               Update Assignee
```

#### 4.4.3 Dispatch Flow

```
User → Create Dispatch → Add Items → Calculate Totals
                                     ↓
                               Create MachineDispatch
                                     ↓
                               Create StockHistory
                                     ↓
                               Generate Challan (optional)
```

### 4.5 Authentication Flow

The system uses a custom session-based authentication:

```
Login → Validate Credentials → Create Session → Set sgi_user_id
                                          ↓
                                  Redirect to Dashboard
                                          ↓
                                  Session Validation on Each Request
```

---

## 5. Installation & Setup

### 5.1 Prerequisites

Before installing SGI ERP, ensure you have:

1. **Python 3.11.9** or higher installed
2. **MySQL 5.7** or higher installed and running
3. **Git** for version control
4. **pip** package manager
5. Virtual environment tool (venv or virtualenv)

### 5.2 Installation Steps

#### Step 1: Clone the Repository

```bash
git clone https://github.com/nishitkumawat/esp-backend.git
cd esp-backend
```

#### Step 2: Create Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On Linux/Mac
source venv/bin/activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages include:
- Django==5.0.2
- mysqlclient
- python-dotenv
- cloudinary
- django-storages
- pillow
- pytz

#### Step 4: Configure Database

Create a MySQL database:

```sql
CREATE DATABASE sgi_erp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sgi_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON sgi_erp.* TO 'sgi_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Step 5: Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_NAME=sgi_erp
DB_USER=sgi_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-secret-key-here
DEBUG=True
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

#### Step 6: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 7: Create Superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin user.

#### Step 8: Collect Static Files

```bash
python manage.py collectstatic
```

#### Step 9: Run Development Server

```bash
python manage.py runserver
```

Access the application at `http://127.0.0.1:8000/sgi_erp/`

### 5.3 Production Deployment

#### 5.3.1 Web Server Configuration

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

#### 5.3.2 Nginx Configuration

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /sgi_erp/static/ {
        alias /path/to/static/files/;
    }

    location /sgi_erp/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 5.3.3 Security Settings

In production, ensure:
- `DEBUG = False` in settings
- Use HTTPS
- Configure CORS properly
- Set secure cookie flags
- Use strong secret keys

### 5.4 Backup and Restore

#### 5.4.1 Database Backup

```bash
mysqldump -u sgi_user -p sgi_erp > backup_$(date +%Y%m%d).sql
```

#### 5.4.2 Database Restore

```bash
mysql -u sgi_user -p sgi_erp < backup_20261027.sql
```

#### 5.4.3 Media Backup

Backup the Cloudinary media files or configure automatic backups.

---

## 6. Features & Modules

### 6.1 Authentication Module

#### 6.1.1 Login System

- Custom session-based authentication
- Email and password login
- Session management with `sgi_user_id`
- Automatic session timeout
- Secure password hashing

#### 6.1.2 User Roles

The system supports two roles:

**Admin:**
- Full system access
- User management
- Settings configuration
- All CRUD operations

**Operator:**
- Inventory operations
- Stock movements
- Dispatch creation
- Limited administrative access

#### 6.1.3 User Profile

Extended user profile includes:
- Role assignment
- Active status
- Creation tracking
- Last login timestamp

### 6.2 Inventory Module

#### 6.2.1 Item Management

**Features:**
- Create items with unique codes
- Define item categories
- Specify units of measurement
- Active/inactive status
- Bulk item operations

**Fields:**
- Code (unique identifier)
- Name
- Category
- Unit (kg, pcs, meters, etc.)
- Description
- Status (active/inactive)

#### 6.2.2 Catalog View

- Browse all items
- Filter by category
- Filter by status
- Search functionality
- Quick actions (view, edit, add stock, delete)

#### 6.2.3 Process-Based Inventory

- Track items through manufacturing processes
- Assign items to specific processes
- Monitor stock at each process stage
- Process completion tracking

#### 6.2.4 Stock Allocation

- Assign stock to workers/assignees
- Track who has what stock
- Timestamped assignments
- Reassignment capabilities

#### 6.2.5 Stock History

- Complete audit trail
- Movement types:
  - Initial Stock
  - Stock Movement
  - Dispatch
  - Adjustment
- Performed-by tracking
- Timestamp recording
- Item snapshots for historical accuracy

### 6.3 Manufacturing Module

#### 6.3.1 Process Management

**Features:**
- Define manufacturing workflow stages
- Set process order
- Mark processes as completed
- Active/inactive status
- Process hierarchy

**Process Types:**
- Regular Process: Ongoing manufacturing stage
- Completed Process: Final output stage

#### 6.3.2 Process Stock View

- Visual stock distribution by process
- Progress bars showing completion
- Quantity breakdown
- Color-coded by status

#### 6.3.3 Assignee Management

**Features:**
- Create worker/assignee profiles
- Department assignment
- Active status
- Assignee-based stock view

**Fields:**
- Name
- Department
- Status (active/inactive)
- Created by tracking

### 6.4 Dispatch Module

#### 6.4.1 Machine Management

**Features:**
- Create machine profiles
- Set machine capacity
- Active/inactive status
- Machine-based dispatch

**Fields:**
- Code (unique identifier)
- Name
- Description
- Capacity
- Status

#### 6.4.2 Dispatch Creation

**Features:**
- Create dispatch records
- Link to machine
- Add multiple items
- Customer information
- Invoice tracking
- Date management

**Dispatch Fields:**
- Machine
- Customer name
- Invoice number
- Dispatch date
- Items and quantities
- Performed by

#### 6.4.3 Dispatch Tracking

- View all dispatches
- Filter by machine
- Filter by date range
- Search functionality
- Dispatch details view

#### 6.4.4 Challan Generation

- Generate delivery challans
- Party/company details
- Item listing with quantities
- Process information
- Date and remarks
- Print/Export functionality

### 6.5 Challan Module

#### 6.5.1 Challan Types

- **Outward:** Stock sent to external parties
- **Inward:** Stock received from external parties

#### 6.5.2 Challan Creation

**Features:**
- Create challans for stock movements
- Add multiple items
- Specify assignee
- Set challan type
- Add remarks
- Auto-generated challan numbers (CH-YYYY-NNNN)

#### 6.5.3 Challan Management

- View all challans
- Filter by type
- Filter by date range
- Search by party name
- View challan details
- Print challan PDF

#### 6.5.4 Challan Items

Each challan item includes:
- Product
- Process
- Quantity
- Unit
- Remarks

### 6.6 Dashboard Module

#### 6.6.1 Overview Statistics

- Total Items count
- Active Entries count
- Completed Units count
- Total Machines count
- Dispatches Today count

#### 6.6.2 Recent Activity

- Latest stock movements
- Item and quantity details
- Process and assignee information
- Time-ago display
- Quick access to details

#### 6.6.3 Stock by Process

- Visual distribution chart
- Progress bars for each process
- Color-coded completion status
- Total stock calculation

#### 6.6.4 Quick Actions

- Add Item
- Move Stock
- New Dispatch
- Add Machine

### 6.7 Settings Module

#### 6.7.1 Process Configuration

- Add/edit manufacturing processes
- Set process order
- Define process type
- Manage process status
- Track created by information

#### 6.7.2 Assignee Configuration

- Add/edit workers
- Assign departments
- Manage assignee status
- Track created by information

#### 6.7.3 User Management

- Add/edit ERP users
- Assign roles (admin/operator)
- Manage user status
- Reset user access

### 6.8 Reporting Module

#### 6.8.1 Inventory Reports

- Current stock levels
- Process-wise distribution
- Assignee-wise allocation
- Item-wise history

#### 6.8.2 Dispatch Reports

- Dispatch history
- Machine-wise dispatches
- Date range reports
- Customer-wise dispatches

#### 6.8.3 Activity Reports

- Stock movement history
- User activity logs
- System events
- Audit trails

---

## 7. User Guide

### 7.1 Getting Started

#### 7.1.1 First Login

1. Navigate to the SGI ERP login page
2. Enter your email and password
3. Click "Login"
4. You will be redirected to the dashboard

#### 7.1.2 Dashboard Navigation

The dashboard provides:
- Overview statistics
- Recent activity feed
- Stock distribution by process
- Quick action buttons

### 7.2 Inventory Operations

#### 7.2.1 Adding Items

1. Navigate to Inventory → Catalog
2. Click "Add Item"
3. Fill in the required fields:
   - Code (unique identifier)
   - Name
   - Category
   - Unit
   - Description (optional)
4. Click "Save"

#### 7.2.2 Adding Stock

1. Navigate to Inventory → Add Stock
2. Select the item from the dropdown
3. Select the process
4. Enter the quantity
5. Select the assignee (optional)
6. Click "Add Stock"

The system will:
- Create an inventory entry
- Record the stock history
- Update dashboard statistics

#### 7.2.3 Moving Stock

1. Navigate to Inventory → Move Stock
2. Select the source item and process
3. Select the target process
4. Enter the quantity to move
5. Select the target assignee (optional)
6. Click "Move Stock"

The system will:
- Validate the stock availability
- Convert the stock to the new process
- Create a new inventory entry
- Record the movement in history
- Update the source and target entries

#### 7.2.4 Viewing Inventory

1. Navigate to Inventory
2. View all stock entries
3. Use filters to narrow down:
   - Search by item code or name
   - Filter by process status
   - Filter by specific process
   - Filter by status
4. Click on an entry to view details
5. Use action buttons to:
   - View item details
   - Move stock
   - Delete entry

#### 7.2.5 Managing Categories

Items are automatically categorized based on the category field. To manage categories:
1. Navigate to Inventory → Catalog
2. Use the category filter to view items by category
3. Edit items to change their category

### 7.3 Manufacturing Operations

#### 7.3.1 Creating Processes

1. Navigate to Settings
2. In the "Manufacturing Processes" section
3. Click "Add"
4. Fill in:
   - Order (sequence number)
   - Name
   - Type (Process or Completed)
5. Click "Save"

#### 7.3.2 Managing Assignees

1. Navigate to Settings
2. In the "Assignees" section
3. Click "Add Assignee"
4. Fill in:
   - Name
   - Department (optional)
5. Click "Save"

#### 7.3.3 Viewing Process Stock

1. Navigate to Dashboard
2. View the "Stock by Process" section
3. Progress bars show distribution
4. Click "View All" to see detailed inventory

### 7.4 Dispatch Operations

#### 7.4.1 Creating Machines

1. Navigate to Machines
2. Click "Add Machine"
3. Fill in:
   - Code
   - Name
   - Description (optional)
   - Capacity (optional)
4. Click "Save"

#### 7.4.2 Creating Dispatches

1. Navigate to Dispatch → New Dispatch
2. Select the machine
3. Enter customer details:
   - Customer name
   - Invoice number
   - Dispatch date
4. Add items:
   - Select item
   - Enter quantity
   - Click "Add Item"
5. Click "Create Dispatch"

The system will:
- Create the dispatch record
- Record stock as dispatched
- Generate a challan if configured
- Update dashboard statistics

#### 7.4.3 Viewing Dispatches

1. Navigate to Dispatch History
2. View all dispatches
3. Use filters:
   - Search by customer, machine, invoice
   - Filter by machine
   - Filter by date range
4. Click on a dispatch to view details
5. View associated challan if available

### 7.5 Challan Operations

#### 7.5.1 Creating Challans

1. Navigate to Challans (if enabled in sidebar)
2. Click "New Challan"
3. Fill in:
   - Party/Company name
   - Assignee
   - Type (Outward/Inward)
   - Date
   - Remarks (optional)
4. Add items:
   - Select product
   - Select process
   - Enter quantity
   - Enter unit
   - Click "Add Item"
5. Click "Create Challan"

#### 7.5.2 Viewing Challans

1. Navigate to Challans
2. View all challans
3. Use filters:
   - Search by party name
   - Filter by type
   - Filter by date range
4. Click on a challan to view details
5. Click "Print" to generate PDF

#### 7.5.3 Printing Challans

1. Open a challan detail view
2. Click "Print"
3. The system generates a PDF challan
4. The PDF includes:
   - Challan number and date
   - Party/Company details
   - Item list with quantities
   - Process information
   - Total quantities
   - Remarks

### 7.6 User Management

#### 7.6.1 Adding Users

1. Navigate to Settings
2. In the "ERP Users" section
3. Click "Add User"
4. Fill in:
   - Username
   - Email
   - Password
   - Role (Admin/Operator)
5. Click "Save"

#### 7.6.2 Managing User Roles

**Admin Role:**
- Full system access
- Can add/edit users
- Can access settings
- Can perform all operations

**Operator Role:**
- Can manage inventory
- Can create dispatches
- Cannot access user management
- Cannot modify system settings

### 7.7 Filtering and Search

All list views support filtering:

#### 7.7.1 Search

- Enter search terms in the search box
- Searches across relevant fields
- Real-time filtering

#### 7.7.2 Dropdown Filters

- Select from predefined options
- Multiple filters can be combined
- Click "Apply" to filter
- Click "Clear" to reset filters

### 7.8 Mobile Usage

The system is mobile-responsive:

- Filters are hidden on mobile for cleaner interface
- Buttons stack vertically on mobile
- Tables support horizontal scrolling
- Touch-friendly button sizes
- Optimized for common mobile screen sizes

---

## 8. Workflow Processes

### 8.1 Stock Management Workflow

#### 8.1.1 Initial Stock Entry

```
Start → Select Item → Select Process → Enter Quantity → 
Select Assignee → Validate → Create Entry → 
Record History → Update Dashboard → End
```

**Validation Rules:**
- Item must exist
- Process must exist
- Quantity must be positive
- Assignee must be active (if selected)

**Data Recorded:**
- ItemProcess entry with item, process, quantity
- StockHistory entry with movement type "initial"
- Created by information
- Timestamp

#### 8.1.2 Stock Movement

```
Start → Select Source Item/Process → Enter Quantity → 
Select Target Process → Select Target Assignee → 
Validate Availability → Convert Stock → 
Create New Entry → Record History → 
Update Source Entry → Update Dashboard → End
```

**Validation Rules:**
- Source entry must exist
- Sufficient quantity must be available
- Target process must exist
- Quantity must be positive
- Cannot move to same process

**Data Recorded:**
- New ItemProcess entry for target
- StockHistory entry with movement type "move"
- Source and target information
- Performed by information
- Timestamp

#### 8.1.3 Stock Adjustment

```
Start → Select Entry → Enter Adjustment Quantity → 
Select Adjustment Type (Add/Remove) → 
Validate → Update Entry → 
Record History → Update Dashboard → End
```

**Use Cases:**
- Correcting errors
- Manual adjustments
- Damaged stock removal
- Unexpected additions

### 8.2 Manufacturing Workflow

#### 8.2.1 Process Definition

```
Define Process → Set Order → Set Type → 
Mark Active → Link to Items → Save → 
Available for Stock Allocation
```

**Process Types:**
- **Regular Process:** Intermediate manufacturing stage
- **Completed Process:** Final output stage

**Best Practices:**
- Order processes logically
- Use descriptive names
- Mark completed processes correctly
- Keep processes active unless deprecated

#### 8.2.2 Stock Through Process

```
Initial Stock → Process 1 → Process 2 → ... → 
Completed Process → Dispatch
```

**Tracking:**
- Each stage has separate inventory entry
- Quantities can vary at each stage
- Complete audit trail maintained
- Stock history shows all movements

#### 8.2.3 Assignee Allocation

```
Create Assignee → Set Department → Mark Active → 
Assign Stock → Track Ownership → 
Reassign as Needed → End
```

**Benefits:**
- Clear ownership tracking
- Accountability
- Easy reassignment
- Department-wise reporting

### 8.3 Dispatch Workflow

#### 8.3.1 Dispatch Creation

```
Start → Select Machine → Enter Customer Details → 
Add Items → Calculate Totals → 
Validate Stock → Create Dispatch → 
Record History → Generate Challan → 
Update Inventory → Update Dashboard → End
```

**Validation Rules:**
- Machine must exist
- Customer name required
- At least one item required
- Sufficient stock available
- Dispatch date valid

**Data Recorded:**
- MachineDispatch entry
- StockHistory entry with movement type "dispatch"
- Challan (if applicable)
- All item details
- Performed by information

#### 8.3.2 Challan Generation

```
Dispatch Created → Auto-Generate Challan → 
Add Party Details → Add Items → 
Set Date → Generate PDF → 
Save Record → Available for Print
```

**Challan Contents:**
- Unique challan number
- Date
- Party/Company name
- Assignee information
- Item list with:
  - Product name
  - Process
  - Quantity
  - Unit
- Total quantities
- Remarks

### 8.4 User Management Workflow

#### 8.4.1 User Creation

```
Start → Enter User Details → Select Role → 
Set Password → Validate → Create User → 
Create Profile → Set Active → 
Notify User → End
```

**Role Assignment:**
- Admin: Full access
- Operator: Limited access
- Cannot be changed without appropriate permissions

#### 8.4.2 Session Management

```
Login → Validate Credentials → Create Session → 
Set sgi_user_id → Redirect to Dashboard → 
Validate on Each Request → Session Timeout → 
Logout → Clear Session → Redirect to Login
```

**Security Features:**
- Session-based authentication
- Automatic timeout
- Secure session handling
- Logout clears all session data

---

## 9. Database Schema

### 9.1 ERPUserProfile

Extended user profile for SGI ERP users.

**Fields:**
- `user` (OneToOneField to User): Linked Django user
- `role` (CharField): admin or operator
- `is_erp_active` (BooleanField): Active status
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp

**Indexes:**
- user_id (unique)
- role
- is_erp_active

### 9.2 Item

Product/item master data.

**Fields:**
- `code` (CharField, unique): Item code
- `name` (CharField): Item name
- `category` (CharField): Item category
- `unit` (CharField): Unit of measurement
- `description` (TextField, optional): Item description
- `is_active` (BooleanField): Active status
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp

**Indexes:**
- code (unique)
- category
- is_active

### 9.3 Process

Manufacturing process definitions.

**Fields:**
- `name` (CharField): Process name
- `order` (IntegerField): Process order
- `is_active` (BooleanField): Active status
- `is_completed_process` (BooleanField): Completion status
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp
- `created_by` (ForeignKey to User): Creator

**Indexes:**
- order
- is_active
- is_completed_process

### 9.4 ItemProcess

Junction table linking items to processes with quantities.

**Fields:**
- `item` (ForeignKey to Item): Related item
- `process` (ForeignKey to Process): Related process
- `quantity` (DecimalField): Stock quantity
- `assigned_to` (ForeignKey to Assignee, optional): Assignee
- `assigned_at` (DateTimeField): Assignment timestamp
- `updated_at` (DateTimeField): Last update timestamp

**Indexes:**
- (item, process) composite
- process
- assigned_to
- updated_at

### 9.5 Assignee

Worker/assignee profiles.

**Fields:**
- `name` (CharField): Assignee name
- `department` (CharField, optional): Department
- `is_active` (BooleanField): Active status
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp
- `created_by` (ForeignKey to User): Creator

**Indexes:**
- name
- is_active

### 9.6 StockHistory

Audit trail for all stock movements.

**Fields:**
- `item` (ForeignKey to Item): Related item
- `from_process` (ForeignKey to Process, optional): Source process
- `to_process` (ForeignKey to Process, optional): Target process
- `from_assignee` (ForeignKey to Assignee, optional): Source assignee
- `to_assignee` (ForeignKey to Assignee, optional): Target assignee
- `quantity` (DecimalField): Quantity moved
- `movement_type` (CharField): initial, move, dispatch, adjustment
- `item_code_snapshot` (CharField): Item code snapshot
- `item_name_snapshot` (CharField): Item name snapshot
- `performed_by` (ForeignKey to User): User who performed action
- `created_at` (DateTimeField): Creation timestamp

**Indexes:**
- created_at
- item
- from_process
- to_process
- movement_type

### 9.7 Machine

Manufacturing machine profiles.

**Fields:**
- `code` (CharField, unique): Machine code
- `name` (CharField): Machine name
- `description` (TextField, optional): Description
- `capacity` (DecimalField, optional): Capacity
- `is_active` (BooleanField): Active status
- `created_at` (DateTimeField): Creation timestamp
- `updated_at` (DateTimeField): Last update timestamp

**Indexes:**
- code (unique)
- is_active

### 9.8 MachineDispatch

Dispatch records linked to machines.

**Fields:**
- `machine` (ForeignKey to Machine): Related machine
- `customer_name` (CharField): Customer name
- `invoice_number` (CharField, optional): Invoice number
- `dispatch_date` (DateField): Dispatch date
- `created_at` (DateTimeField): Creation timestamp
- `created_by` (ForeignKey to User): Creator

**Indexes:**
- machine
- dispatch_date
- created_at

### 9.9 MachineDispatchItem

Items within a machine dispatch.

**Fields:**
- `dispatch` (ForeignKey to MachineDispatch): Related dispatch
- `item` (ForeignKey to Item): Related item
- `process` (ForeignKey to Process): Related process
- `quantity` (DecimalField): Quantity
- `unit` (CharField): Unit

### 9.10 Challan

Delivery challan documents.

**Fields:**
- `challan_number` (CharField, unique): Challan number
- `party_name` (CharField): Party/company name
- `assignee` (ForeignKey to Assignee, optional): Assignee
- `challan_type` (CharField): outward or inward
- `date` (DateField): Challan date
- `remarks` (TextField, optional): Remarks
- `created_at` (DateTimeField): Creation timestamp
- `created_by` (ForeignKey to User): Creator

**Indexes:**
- challan_number (unique)
- date
- challan_type

### 9.11 ChallanItem

Items within a challan.

**Fields:**
- `challan` (ForeignKey to Challan): Related challan
- `item` (ForeignKey to Item): Related item
- `process` (ForeignKey to Process): Related process
- `quantity` (DecimalField): Quantity
- `unit` (CharField): Unit
- `remarks` (TextField, optional): Remarks

---

## 10. API Documentation

### 10.1 URL Structure

The system uses Django's URL routing with namespace `sgierp`.

**Base URL:** `/sgi_erp/`

### 10.2 Authentication Endpoints

#### 10.2.1 Login

- **URL:** `/sgi_erp/login/`
- **Method:** POST
- **Parameters:**
  - `email`: User email
  - `password`: User password
- **Response:** Redirects to dashboard on success

#### 10.2.2 Logout

- **URL:** `/sgi_erp/logout/`
- **Method:** GET
- **Response:** Redirects to login page

### 10.3 Inventory Endpoints

#### 10.3.1 Inventory List

- **URL:** `/sgi_erp/inventory/`
- **Method:** GET
- **Query Parameters:**
  - `q`: Search term
  - `process_status`: non_completed, completed, all
  - `process`: Process ID
  - `status`: active, inactive
- **Response:** HTML page with inventory list

#### 10.3.2 Add Stock

- **URL:** `/sgi_erp/inventory/add/`
- **Method:** POST
- **Parameters:**
  - `item`: Item ID
  - `process`: Process ID
  - `quantity`: Quantity value
  - `assignee`: Assignee ID (optional)
- **Response:** Redirects to inventory list

#### 10.3.3 Move Stock

- **URL:** `/sgi_erp/inventory/move/`
- **Method:** POST
- **Parameters:**
  - `source_item`: Source ItemProcess ID
  - `target_process`: Target Process ID
  - `quantity`: Quantity to move
  - `target_assignee`: Target Assignee ID (optional)
- **Response:** Redirects to inventory list

#### 10.3.4 Item Catalog

- **URL:** `/sgi_erp/inventory/catalog/`
- **Method:** GET
- **Query Parameters:**
  - `q`: Search term
  - `category`: Category filter
  - `status`: Status filter
- **Response:** HTML page with item catalog

#### 10.3.5 Stock History

- **URL:** `/sgi_erp/inventory/history/`
- **Method:** GET
- **Query Parameters:**
  - `q`: Search term
  - `type`: Movement type filter
- **Response:** HTML page with stock history

### 10.4 Manufacturing Endpoints

#### 10.4.1 Process Management

- **Create:** `/sgi_erp/settings/process/create/` (POST)
- **Edit:** `/sgi_erp/settings/process/<id>/edit/` (POST)
- **Delete:** `/sgi_erp/settings/process/<id>/delete/` (POST)

#### 10.4.2 Assignee Management

- **Create:** `/sgi_erp/settings/assignee/create/` (POST)
- **Edit:** `/sgi_erp/settings/assignee/<id>/edit/` (POST)
- **Delete:** `/sgi_erp/settings/assignee/<id>/delete/` (POST)

### 10.5 Dispatch Endpoints

#### 10.5.1 Machine Management

- **List:** `/sgi_erp/machines/` (GET)
- **Create:** `/sgi_erp/machines/create/` (POST)
- **Detail:** `/sgi_erp/machines/<id>/` (GET)
- **Edit:** `/sgi_erp/machines/<id>/edit/` (POST)

#### 10.5.2 Dispatch Management

- **List:** `/sgi_erp/dispatch/` (GET)
- **Create:** `/sgi_erp/dispatch/create/` (POST)
- **Detail:** `/sgi_erp/dispatch/<id>/` (GET)
- **Challan:** `/sgi_erp/dispatch/<id>/challan/` (GET)

### 10.6 Challan Endpoints

#### 10.6.1 Challan Management

- **List:** `/sgi_erp/challans/` (GET)
- **Create:** `/sgi_erp/challans/new/` (POST)
- **Detail:** `/sgi_erp/challans/<id>/` (GET)
- **Print:** `/sgi_erp/challans/<id>/print/` (GET)

### 10.7 User Management Endpoints

#### 10.7.1 User Management

- **Create:** `/sgi_erp/settings/user/create/` (POST)
- **Edit:** `/sgi_erp/settings/user/<id>/edit/` (POST)

### 10.8 Dashboard Endpoints

#### 10.8.1 Dashboard

- **URL:** `/sgi_erp/dashboard/`
- **Method:** GET
- **Response:** HTML page with dashboard statistics and activity

---

## 11. Security

### 11.1 Authentication

#### 11.1.1 Session-Based Authentication

The system uses Django's session framework with custom session keys:

- **Session Key:** `sgi_user_id`
- **Storage:** Database-backed sessions
- **Timeout:** Configurable (default: 2 weeks)
- **Security:** Signed cookies

#### 11.1.2 Password Security

- Passwords are hashed using Django's PBKDF2 algorithm
- Salt is included in the hash
- Minimum password length: 8 characters
- Password complexity: No specific requirements (can be configured)

#### 11.1.3 Custom Decorators

The system includes custom authentication decorators:

- `@sgi_login_required`: Redirects to login if not authenticated
- `@sgi_admin_required`: Redirects to dashboard if not admin
- Both decorators check for `sgi_user_id` in session

### 11.2 Authorization

#### 11.2.1 Role-Based Access Control

**Admin Role:**
- Full system access
- User management
- Settings configuration
- All CRUD operations

**Operator Role:**
- Inventory operations
- Stock movements
- Dispatch creation
- Limited access to settings

#### 11.2.2 Permission Checks

Permission checks are performed at:
- View level (decorators)
- Template level (conditional rendering)
- Form level (validation)

### 11.3 Data Security

#### 11.3.1 SQL Injection Prevention

- Django ORM prevents SQL injection
- All database queries use parameterized queries
- No raw SQL queries in production code

#### 11.3.2 XSS Prevention

- Django templates auto-escape HTML
- User input is sanitized
- CSRF protection enabled on all forms

#### 11.3.3 CSRF Protection

- CSRF tokens are included in all forms
- Tokens are validated on POST requests
- Token regeneration on each session

### 11.4 Session Security

#### 11.4.1 Secure Cookies

- `SESSION_COOKIE_SECURE`: True in production
- `SESSION_COOKIE_HTTPONLY`: True
- `SESSION_COOKIE_SAMESITE`: 'Lax'

#### 11.4.2 Session Timeout

- Sessions expire after configured timeout
- Activity updates session expiry
- Logout clears all session data

### 11.5 Password Recovery

Currently not implemented. Can be added using Django's built-in password reset views.

### 11.6 Security Best Practices

#### 11.6.1 Recommended Configurations

- Use HTTPS in production
- Set `DEBUG = False`
- Use strong `SECRET_KEY`
- Configure allowed hosts
- Use environment variables for sensitive data
- Regular security updates

#### 11.6.2 Monitoring

- Monitor failed login attempts
- Monitor unusual activity patterns
- Regular security audits
- Log all administrative actions

---

## 12. Performance Optimization

### 12.1 Database Optimization

#### 12.1.1 Indexing

Strategic indexes have been added to frequently queried fields:

- `Item.code`, `Item.category`, `Item.is_active`
- `Process.order`, `Process.is_active`, `Process.is_completed_process`
- `ItemProcess` composite index on (item, process)
- `ItemProcess.process`, `ItemProcess.assigned_to`, `ItemProcess.updated_at`
- `Assignee.name`, `Assignee.is_active`
- `StockHistory.created_at`, `StockHistory.item`, `StockHistory.movement_type`

#### 12.1.2 Query Optimization

**select_related Optimization:**
- Used for foreign key relationships
- Reduces N+1 query problems
- Applied in authentication views

**prefetch_related Optimization:**
- Used for many-to-many relationships
- Reduces query count
- Applied in inventory views

**only() Optimization:**
- Fetches only required fields
- Reduces memory usage
- Applied in list views

**bulk_fetch Optimization:**
- Fetches multiple objects in single query
- Applied in challan creation
- Applied in stock conversion

### 12.2 Caching Strategy

#### 12.2.1 Static File Caching

- Static files served via CDN (Cloudinary)
- Browser caching headers configured
- Long cache periods for static assets

#### 12.2.2 Database Query Caching

- Django's built-in query caching
- Session-based caching for frequent queries
- Can be extended with Redis for production

### 12.3 Frontend Optimization

#### 12.3.1 CSS Optimization

- Minified CSS in production
- CSS variables for theming
- Efficient selectors
- Mobile-first approach

#### 12.3.2 JavaScript Optimization

- Minimal JavaScript usage
- No external frameworks
- Lazy loading where applicable
- Event delegation

#### 12.3.3 Image Optimization

- Images served via Cloudinary
- Automatic format conversion
- Responsive image loading
- Lazy loading for below-fold images

### 12.4 Response Time Optimization

#### 12.4.1 Pagination

- List views use pagination
- Configurable page size (default: 20)
- Reduces initial page load time

#### 12.4.2 Lazy Loading

- Large lists implement pagination
- Heavy computations deferred
- Background processing for reports

### 12.5 Mobile Optimization

#### 12.5.1 Responsive Design

- Mobile-first CSS
- Touch-friendly targets
- Optimized for common mobile devices
- Filters hidden on mobile for cleaner interface

#### 12.5.2 Performance

- Reduced CSS on mobile
- No heavy JavaScript
- Optimized images
- Minimal DOM elements

### 12.6 Monitoring and Profiling

#### 12.6.1 Django Debug Toolbar

Recommended for development:
- Query analysis
- Request profiling
- Performance metrics

#### 12.6.2 Production Monitoring

Recommended tools:
- Django Silk for query profiling
- Sentry for error tracking
- New Relic for application monitoring

---

## 13. Troubleshooting

### 13.1 Common Issues

#### 13.1.1 Login Issues

**Problem:** Cannot login to the system

**Solutions:**
1. Verify username and password
2. Check if user account is active
3. Clear browser cookies
4. Check session configuration
5. Verify database connection

#### 13.1.2 Database Connection Issues

**Problem:** Cannot connect to database

**Solutions:**
1. Verify MySQL is running
2. Check database credentials in .env
3. Verify database exists
4. Check MySQL user permissions
5. Test connection with MySQL client

#### 13.1.3 Migration Errors

**Problem:** Migrations fail to apply

**Solutions:**
1. Check for conflicting migrations
2. Use `python manage.py showmigrations` to check status
3. Use `python manage.py migrate --fake` if needed
4. Check database schema
5. Verify model definitions

#### 13.1.4 Static File Issues

**Problem:** Static files not loading

**Solutions:**
1. Run `python manage.py collectstatic`
2. Check STATIC_URL in settings
3. Verify STATIC_ROOT configuration
4. Check file permissions
5. Clear browser cache

#### 13.1.5 Permission Errors

**Problem:** Permission denied errors

**Solutions:**
1. Check user role assignment
2. Verify decorator usage
3. Check session validity
4. Review URL configuration
5. Verify view permissions

### 13.2 Performance Issues

#### 13.2.1 Slow Page Loads

**Solutions:**
1. Check database query count
2. Enable query logging
3. Review indexes
4. Check for N+1 queries
5. Implement caching

#### 13.2.2 Memory Issues

**Solutions:**
1. Check for memory leaks
2. Review query result sets
3. Implement pagination
4. Use `only()` to limit fields
5. Restart application server

### 13.3 Error Handling

#### 13.3.1 Common Error Messages

**"VariableDoesNotExist"**
- Template variable missing
- Check context in view
- Verify variable name

**"IntegrityError"**
- Database constraint violation
- Check unique constraints
- Verify foreign key relationships

**"ValidationError"**
- Form validation failed
- Check form fields
- Verify data types

#### 13.3.2 Error Logging

Error logging is configured to:
- Log to console in development
- Log to file in production
- Include stack traces
- Include request information

### 13.4 Debug Mode

#### 13.4.1 Enabling Debug Mode

Set in settings.py:
```python
DEBUG = True
```

#### 13.4.2 Debug Toolbar

Install:
```bash
pip install django-debug-toolbar
```

Add to INSTALLED_APPS and MIDDLEWARE in settings.py.

### 13.5 Resetting the System

#### 13.5.1 Database Reset

Use the custom management command:
```bash
python manage.py reset_erp
```

This will:
- Delete all ERP users
- Delete all inventory entries
- Delete all processes
- Delete all assignees
- Delete all machines
- Delete all dispatches
- Delete all challans
- Keep migrations intact

#### 13.5.2 Creating Fresh Admin User

After reset:
```bash
python manage.py createsuperuser
```

### 13.6 Getting Help

#### 13.6.1 Documentation

Refer to this documentation for:
- System overview
- Feature descriptions
- User guides
- Technical details

#### 13.6.2 Support Contacts

- Development Team: [Contact Information]
- IT Support: [Contact Information]
- System Administrator: [Contact Information]

---

## 14. Maintenance

### 14.1 Regular Maintenance Tasks

#### 14.1.1 Database Maintenance

**Weekly:**
- Check database size
- Review slow queries
- Check index usage
- Verify backup integrity

**Monthly:**
- Optimize database tables
- Update statistics
- Review and clean old data
- Archive historical data if needed

**Quarterly:**
- Full database backup
- Performance review
- Security audit
- Update dependencies

#### 14.1.2 Application Maintenance

**Weekly:**
- Check error logs
- Monitor performance metrics
- Review user activity
- Check disk space

**Monthly:**
- Update Python packages
- Review security patches
- Test disaster recovery
- Update documentation

**Quarterly:**
- Full system backup
- Security review
- Performance optimization
- Feature review and planning

### 14.2 Backup Strategy

#### 14.2.1 Database Backups

**Daily Backups:**
- Automated daily backups
- Retain 7 days
- Offsite storage

**Weekly Backups:**
- Full weekly backups
- Retain 4 weeks
- Offsite storage

**Monthly Backups:**
- Full monthly backups
- Retain 12 months
- Offsite storage

#### 14.2.2 Media Backups

- Cloudinary automatic backups
- Periodic verification
- Restore testing

#### 14.2.3 Code Backups

- Git version control
- Regular commits
- Tagged releases
- Repository backup

### 14.3 Updates and Upgrades

#### 14.3.1 Django Updates

**Process:**
1. Review release notes
2. Test in development environment
3. Update requirements.txt
4. Run migrations
5. Test thoroughly
6. Deploy to production

#### 14.3.2 Python Updates

**Process:**
1. Review Python version compatibility
2. Test in development
3. Update virtual environment
4. Test all functionality
5. Deploy to production

#### 14.3.3 Dependency Updates

**Process:**
1. Review available updates
2. Check for security vulnerabilities
3. Test in development
4. Update requirements.txt
5. Deploy to production

### 14.4 Monitoring

#### 14.4.1 Application Monitoring

**Metrics to Monitor:**
- Response times
- Error rates
- User activity
- Database performance
- Server resources

**Tools:**
- Django Debug Toolbar (development)
- Django Silk (production)
- Sentry (error tracking)
- New Relic (APM)

#### 14.4.2 Database Monitoring

**Metrics to Monitor:**
- Query performance
- Connection pool usage
- Table sizes
- Index usage
- Lock contention

**Tools:**
- MySQL slow query log
- Django connection monitoring
- Custom query logging

### 14.5 Security Maintenance

#### 14.5.1 Regular Security Tasks

**Weekly:**
- Review failed login attempts
- Check for unusual activity
- Review user access

**Monthly:**
- Update security patches
- Review user permissions
- Audit administrative access
- Check for vulnerabilities

**Quarterly:**
- Full security audit
- Penetration testing
- Review security policies
- Update documentation

#### 14.5.2 Password Policy

**Recommendations:**
- Minimum 8 characters
- Change every 90 days
- Not shared with others
- Complex characters recommended

### 14.6 Disaster Recovery

#### 14.6.1 Recovery Plan

**Scenarios:**
1. Database corruption
2. Server failure
3. Data loss
4. Security breach

**Recovery Steps:**
1. Identify the issue
2. Assess impact
3. Restore from backup
4. Verify data integrity
5. Test functionality
6. Document incident

#### 14.6.2 Testing Backups

**Process:**
1. Regular restore testing
2. Verify backup integrity
3. Test recovery procedures
4. Update recovery plan
5. Document lessons learned

---

## 15. Future Enhancements

### 15.1 Planned Features

#### 15.1.1 Advanced Reporting

- Custom report builder
- Scheduled reports
- Email reports
- Export to Excel/CSV
- Advanced analytics dashboard

#### 15.1.2 Barcode/QR Code Integration

- Barcode generation for items
- QR code for challans
- Mobile scanning capability
- Quick stock verification

#### 15.1.3 Notifications

- Email notifications for low stock
- SMS alerts for critical events
- In-app notifications
- Notification preferences

#### 15.1.4 Multi-location Support

- Multiple warehouses
- Location-based inventory
- Inter-location transfers
- Location-wise reporting

#### 15.1.5 Advanced Manufacturing

- Bill of Materials (BOM)
- Production planning
- Work order management
- Quality control
- Inspection tracking

### 15.2 Technology Enhancements

#### 15.2.1 Mobile Application

- Native mobile app (iOS/Android)
- Offline capability
- Push notifications
- Camera integration for scanning

#### 15.2.2 API Development

- RESTful API for third-party integration
- API documentation (Swagger/OpenAPI)
- Rate limiting
- API key management

#### 15.2.3 Real-time Updates

- WebSocket integration
- Real-time stock updates
- Live dashboard
- Instant notifications

#### 15.2.4 Machine Learning

- Demand forecasting
- Stock optimization
- Anomaly detection
- Predictive analytics

### 15.3 Integration Opportunities

#### 15.3.1 Accounting Integration

- Integration with accounting software
- Automatic journal entries
- Financial reporting
- Tax calculations

#### 15.3.2 E-commerce Integration

- Inventory sync with e-commerce
- Order management
- Shipping integration
- Payment processing

#### 15.3.3 ERP Integration

- Integration with other ERP systems
- Data synchronization
- Master data management
- Process automation

### 15.4 Process Improvements

#### 15.4.1 Workflow Automation

- Automated stock allocation
- Automatic reorder points
- Process triggers
- Approval workflows

#### 15.4.2 Enhanced User Experience

- Drag-and-drop interfaces
- Advanced filtering
- Saved views
- Personalized dashboards

#### 15.4.3 Collaboration Features

- Comments and annotations
- Task assignments
- Team collaboration
- Document sharing

---

## 16. Appendices

### Appendix A: Glossary

- **ERP:** Enterprise Resource Planning
- **Item:** Product or material tracked in inventory
- **Process:** Manufacturing stage or workflow step
- **Assignee:** Worker or staff member assigned stock
- **Dispatch:** Delivery of goods to customer
- **Challan:** Delivery note or receipt document
- **Stock Movement:** Transfer of stock between processes
- **ORM:** Object-Relational Mapping
- **CRUD:** Create, Read, Update, Delete operations
- **MVC:** Model-View-Controller architecture

### Appendix B: Configuration Reference

#### B.1 Environment Variables

```env
# Database
DB_NAME=sgi_erp
DB_USER=sgi_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret

# Time Zone
TIME_ZONE=Asia/Kolkata
```

#### B.2 Django Settings

Key settings in `backend/settings.py`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'SGIERP',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

STATIC_URL = '/sgi_erp/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/sgi_erp/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### Appendix C: SQL Queries

#### C.1 Common Queries

**Get all active inventory entries:**
```sql
SELECT ip.*, i.code, i.name, p.name as process_name, a.name as assignee_name
FROM SGIERP_itemprocess ip
JOIN SGIERP_item i ON ip.item_id = i.id
JOIN SGIERP_process p ON ip.process_id = p.id
LEFT JOIN SGIERP_assignee a ON ip.assigned_to_id = a.id
WHERE i.is_active = 1 AND p.is_active = 1
ORDER BY i.code, p.order;
```

**Get stock history for an item:**
```sql
SELECT * FROM SGIERP_stockhistory
WHERE item_id = :item_id
ORDER BY created_at DESC;
```

**Get total stock by process:**
```sql
SELECT p.name as process_name, SUM(ip.quantity) as total
FROM SGIERP_itemprocess ip
JOIN SGIERP_process p ON ip.process_id = p.id
JOIN SGIERP_item i ON ip.item_id = i.id
WHERE i.is_active = 1 AND p.is_active = 1
GROUP BY p.id, p.name
ORDER BY p.order;
```

### Appendix D: Code Snippets

#### D.1 Custom Decorator Example

```python
from django.shortcuts import redirect

def sgi_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if 'sgi_user_id' not in request.session:
            return redirect('sgierp:login')
        return view_func(request, *args, **kwargs)
    return wrapper
```

#### D.2 Bulk Fetch Example

```python
# Inefficient (N+1 queries)
for entry in entries:
    item = Item.objects.get(id=entry.item_id)
    process = Process.objects.get(id=entry.process_id)

# Efficient (bulk fetch)
item_ids = [e.item_id for e in entries]
process_ids = [e.process_id for e in entries]
items = {i.id: i for i in Item.objects.filter(id__in=item_ids)}
processes = {p.id: p for p in Process.objects.filter(id__in=process_ids)}
```

### Appendix E: Contact Information

#### E.1 Development Team

- **Project Lead:** [Name]
- **Email:** [Email]
- **Phone:** [Phone]

#### E.2 Support

- **Technical Support:** [Email]
- **Documentation:** [URL]
- **Issue Tracker:** [URL]

### Appendix F: Change Log

#### Version 1.0 (October 2026)
- Initial release
- Core inventory management
- Manufacturing process tracking
- Dispatch management
- Challan generation
- User authentication
- Dashboard and reporting

---

## Document Revision History

| Version | Date | Author | Changes |
|----------|------|--------|---------|
| 1.0 | October 2026 | SGI Development Team | Initial release |

---

**End of Document**
