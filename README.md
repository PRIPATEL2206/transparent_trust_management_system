# Trust Management System

**Project Description:**  
The Trust Management System (TMS) is a web-based application designed to manage the operations of a trust organization. The system allows superusers, admins, and members to interact with various features, including membership management, payments, posts, expenses, group chats, product purchases, and more. It ensures transparency, accountability, and ease of management for all parties involved.

---

## Features

### 1. **User Roles and Permissions**
- **Super Users**: Have full access to edit all elements of the platform.
- **Regular Users**: Can pay to join a trust and receive a payment receipt.
- **Trust Members**: Can create and submit revolutionary ideas (requiring admin approval) and raise expenses (with admin approval).
- **Admin Users**: Can view all members, manage users, monitor payments, and approve or reject requests.

### 2. **Membership and Payment Management**
- Users can join the trust by paying a fee, and payment receipts are generated automatically.
- Admins can set and modify the default membership fee and other configurations.
- All payment and membership activity is tracked for analysis by admins.

### 3. **Revolutionary Ideas and Approvals**
- Trust members can create new revolutionary ideas, which require admin approval before they go live.
- These ideas will have an expiration date and will disappear after a set time.

### 4. **Notices and Requests**
- Members can create notices with requests to admins. Notices have expiration dates and can be edited based on the member's permissions.
  
### 5. **Expense Management**
- Members can raise expense requests, which are approved by admins. These expenses are tracked and stored in the system.
- Members are required to upload receipts for all expenses.
- Admins can download monthly/yearly reports for expenses, donations, and other financial activities.

### 6. **Chat Groups**
- Admins can create internal chat groups and add members to these groups for internal communication.

### 7. **Product Management**
- **Future Features**: Members will be able to add or update new products offered by the trust. Admin approval will be required for the products to be listed.
- Each product will have a discount, and the original price will be calculated based on the discount amount.

### 8. **Fundraising and Donations**
- Trust members can make donations, and all donation receipts will be publicly available to ensure transparency.
- NGOS can request funds, and these requests are managed by the admin.

### 9. **SEO and Web Accessibility**
- The application will be SEO-friendly to ensure it is discoverable in search engines.

### 10. **Login and Authentication**
- Users must log in with their email and password to access the system.
- Permissions for various actions are required and granted by admins.

---

## Installation

### Requirements:
- Python 3.x
- Django 4.x (or the specific version you're using)
- SQLite (default) or PostgreSQL (or another database system)
- Additional libraries: `django-allauth` for authentication, `django-rest-framework` for APIs, `django-crispy-forms` for form handling, etc.

### Setup:

1. **Clone the repository:**

   ```bash
   git clone https://github.com/PRIPATEL2206/transparent_trust_management_system.git

2. **Install Project Dependencies:**
   Install all required Python packages listed in the requirements file:

      ```bash
      pip install -r .\requirements.txt
      ```

   This command ensures all external libraries required by the project are installed.

3. **Create Database Migration Files:**
   Generate migration files based on the current Django models:

   ```bash
   python .\manage.py makemigrations
   ```
    Django analyzes model definitions and prepares database schema changes.
  
  4. **Apply Database Migrations**
     Apply the generated migrations to the database:

     ```bash
     python .\manage.py migrate
      ```
     
      This step creates and updates database tables required by the application.

  

   **Setup Complete**  
    At this stage, the application is successfully configured on your local system.


   ##  How to Run the Application

   1 **Create a Superuser:**
   Create an admin user for accessing the Django admin panel:

   ```bash
   python .\manage.py createsuperuser
   ```

   2 **Run the Django Development Server:**
   Start the development server:

   ```bash
   python .\manage.py runserver
   ```
   
   
   3 **Start Tailwind CSS:**  
    **open another terminal**  
    Navigate to the Tailwind CSS configuration directory and start Tailwind:


   ```bash
   cd .\tailwind_css_conf\
   npm i
   npm run tailwindcss
   ```

   You can now proceed with:
   - Accessing the admin panel
   - Developing or testing application features
