from django.urls import path
from .views import check_ctopupno,get_postpaid,get_prepaid,check_otp,get_gsm_nos,update_gsm_status,refresh_token, get_app_version,add_aadhaar,adhar_api_forward,resend_otp,local_ref_otp,local_ref_otp_verfiy, check_verification_status 
from .caf_pos_view import update_caf_details
urlpatterns = [
    path('check-ctopupno/', check_ctopupno, name='check-ctopupno'),
    path('get-postpaid/', get_postpaid, name='get-postpaid'),
    path('get-prepaid/', get_prepaid, name='get-prepaid'),
    path('check-otp/', check_otp, name='check-otp'),
    path('get-numbers/', get_gsm_nos, name='get-gsm-nos'),
    path('reserve-number/', update_gsm_status, name='update-gsm-status'),
    path('refresh_token/', refresh_token, name='refresh-token'),
    path('get_app_version/', get_app_version, name='get-app-version'),
    path('update_adno/', add_aadhaar, name='add-aadhaar'),
    path('post_caf_data/', update_caf_details, name='post-caf-data'),
    path('adhar_fwd/', adhar_api_forward, name='adhar-api-forward'),
    path('resend_otp/', resend_otp, name='resend-otp'),
    path('local_ref_otp/', local_ref_otp, name='local-ref-otp'),
    path('local_ref_otp_verfiy/', local_ref_otp_verfiy, name='local-ref-otp-verfiy'),
    path('get_act_status/', check_verification_status, name='get-act-status'),

    

    # ... your other URLs
]