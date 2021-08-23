Managing Authentication
=========================

The authentication page controls everything related to user authentication. It has four important features

    * A signup module to create a new user
    * An email verification component to verify the email of a new user and activate their account
    * A login module that logs a verified user
    * A forgot password module to change the password to a new one if the user forget his current password

Signup
-----------

A user can create an account using the signup functionality provided by OWTF.
Signup is a 2-step process

    * A user enters his correct credentials and then an email verification link is sent (shown in terminal if the SMTP server is not set).
    * User then clicks on the email verification link provided to activate his account

.. figure:: /images/signup.png
    :align: center

.. figure:: /images/email_verification.png
    :align: center

    Email verification page where verification link can be resent

.. figure:: /images/email_verification_link.png
    :align: center  
    
    Sample of the email verification link that is sent to the user

Login
-----------

In order for user to login to the application, OWTF provides the login functionality.
Once a user has signed up he can login simply as shown below:

.. figure:: /images/login.png
    :align: center

In case user forgets his password, he can follow the steps shown below to reset a new password.

.. figure:: /images/forgot_password.png
    :align: center

    Provide the username/email of the account for which you want to reset password

.. figure:: /images/otp_sent.png
    :align: center

    Sample of an OTP send to the user

.. figure:: /images/otp_verify.png
    :align: center

    OTP is sent and is required to be verified in this page    

.. figure:: /images/new_password.png
    :align: center

    New password page to reset a new password
