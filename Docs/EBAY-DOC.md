  Webapp: Manage ebay accounts for 30 accounts, 5 employees
  - Manage EBAY Orders
  - Manage EBAY Listings
  - Manage EBAY Customers
  - Manage Products
  - Manage Mail, Messages from EBAY
  Data is imported daily by csv file: Manual Upload or Sync from google sheet or HTTP from chrome extension.
  I need each plan < 25000 tokens.
  Follow the SOLID and YAGNI principles absolutely.
  This is an MVP app.

  Cau 1: Order workflow: Các trạng thái order cần quản lý? (pending, shipped, completed?): Order workflow: Pending, Processing, Shipped, Completed

  Cau 2: Listing workflow: Chỉ view hay cần create/edit listings? Listing: Chỉ cần view và update hàng ngày bằng file csv
  Cau 3: Ưu tiên Phase 1: Trong 5 features, cái nào PHẢI có ngay MVP? Cái nào có thể delay? Order và listing là ưu tiên
  Cau 4: Daily operations: 5 nhân viên làm gì hàng ngày? Role nào? 5 nhan vien hang ngay vao EBAY download csv order, listing, get message EBAY, get email EBAY upload to web app 
  Cau 5: CSV structure: Có sample CSV format không? (orders, listings, customers): Sample csv: Đính kèm ở attach
  Cau 6: Google Sheet: Đã có sheet template chưa? Read-only hay read-write? : Google sheet, chưa có temple
  Cau 7: Chrome Extension: Extension làm gì? Scrape data từ eBay? Chrome extension: Scape data từ ebay bởi vì không sử dụng ebay api
  Cau 8: eBay API: Có plan dùng eBay API không hay chỉ import CSV? EBAY API: không dùng ebay API
  Cau 9: Tech stack hiện tại? Technical: Backend python fast api , database sqlite, front: react + ts + MUI
  Cau 10: Hosting: Deploy ở đâu? (VPS, Vercel, AWS?) Hosting: Chay trên localhost để testing
  Cau 11: Authentication: Simple login hay cần role-based? Authentication: Cần chia mỗi user quản lý 2-3 tài khoản ebay 11.

I would ask some clarifying questions to better understand your project requirements before planning the implementation.

Key Questions for MVP Planning

Data Structure & Integration:

1. CSV Template: You mentioned the sample CSV files attached - can you share sample CSV structures for orders, listings, customers,
products and messages?

- @data

2. Data Relationships: How are orders related to listings? Do you need to track which listings are created for each order?

I have a listing with a number of separate items. I place an order with an item number related to the listing

3. Account Isolation: Should the data be completely isolated per eBay account or do you need cross-account views/reports?

I suspect there will be an account-by-account view and an all-account view. I have my employees have access to 3-5 eBay accounts

User Management & Security:

4. User Roles: You mentioned that each user manages 2-3 eBay accounts. Do you need different levels of permissions (admin, manager, staff)?
My talent is that I only need admin and staff permissions. Admin can access all ebay accounts, staff can only access a few accounts. Admin sets which staff can access which ebay accounts
5. Data Access: Can users view other users' accounts or only their assigned accounts?
Users are allowed to specify viewing of assigned ebay accounts
Core Workflow:
6. Order Processing: What causes order status changes? Manual updates only or automatic based on CSV import?
Manually change order status
7. Duplicate handling: How should the system handle duplicate records when importing CSV files daily?
- Each order will have its own order number. Only import those order numbers that do not exist yet
8. Data validation: What validation rules are important for the data imported? I don't know, please guide me
Performance & Scale:
9. Data volume: Approximately how many orders/lists per account per day/month? Only 5-10 orders/1 account per day

10. Response time: Are there any specific performance requirements for the web interface? Just enough

Chrome Extensions and Google Sheets:
11. Extension integration: Should the Chrome extension load directly into your web application or just export the CSV file? upload chrome extension to web app using http

12. Google Sheets Sync: Want real-time sync or scheduled import from Google Sheets? can't sync real-time. Sync when pressing sync button on web app

Reporting Requirements:
13. Analytics: What key metrics/reports do you need for MVP? (orders, revenue, listing performance?) Today's orders, today's revenue, top selling products, top selling suppliers

14. Export: Do you need to export data back to CSV/Excel for external use? I need to sync to Google Sheet for backup

These answers will help me create a focused, phased implementation plan that strictly adheres to SOLID/YAGNI principles.




