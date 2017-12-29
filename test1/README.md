# Test1 Project
This is the test project for offline exchange. Following is the description of important files of the project so far.

test1 sub directory. It contains the all the setting of django web project. So far it only contains home pages.  In its setting, it expect that mysql is running at the same machine, and it has database called mydb.  In addition, it expect the project directory is MEDIA_ROOT of the website.


users/models.py:  This is the data model that is built based on ...   In addition, it says that qrcode image of each user's paymentmethod will be saved in MEDIA_ROOT/uploads

sql/init_test.sql:  The initialization script to create basic data for the test.


TODO:
(1) Try use django-mysql to improve database query and test capability. (http://django-mysql.readthedocs.io/en/latest/installation.html)


