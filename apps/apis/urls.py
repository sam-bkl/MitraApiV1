from django.urls import path
from .views import check_ctopupno,get_postpaid,get_prepaid,check_otp,get_gsm_nos,update_gsm_status,refresh_token, get_app_version,add_aadhaar,adhar_api_forward,resend_otp,local_ref_otp,local_ref_otp_verfiy, check_verification_status , heartbeat, get_frc_plans, check_vrf_status, release_sim, get_postpaid_plans, upgradation_send_otp,upgradation_verify_otp,upgradation_resend_otp, check_gsm_caf, check_aadhaar_onboarding
from .caf_pos_view import update_caf_details
from .helperviews.mnp_update import get_final_act_status, edit_mnp
from .helperviews.photo_check_view import verify_selfie
from .testapis import get_prepaid_test
from .dkyc.dkyc_view import create_dkyc_record,dkyc_send_otp,dkyc_verify_otp, dkyc_resend_otp,search_bulk_business_groups, get_business_group_details
from .features.gsm_filter_view import search_gsm_numbers
from .features.reserve_numbers import reserve_gsm_number,get_reserved_gsm_numbers
from .external_data.ssdata import get_customer_info,post_to_pre_check
from .features.sim_upgrade.views import create_sim_upgrade_request,get_app_upgrade_options,list_sim_upgrade_requests
from .esim.views import get_esim_by_simnumber,email_verify_otp,email_resend_otp,send_email_otp
from .esim.esim_post_view import update_caf_details_esim
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .sms.views import app_send_otp , app_verify_otp
from .reverification.views import reverify_lookup

urlpatterns = [
    # path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('api/docs/', SpectacularSwaggerView.as_view(url='/cosapp/api/schema/'), name='swagger-ui'),
    # path('api/redoc/', SpectacularSwaggerView.as_view(url='/cosapp/api/schema/'), name='redoc'),
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
    path('frc_plans/', get_frc_plans, name='frc_plans'),
    path('get_final_act_status/',get_final_act_status , name='get-final-act-status'),
    path('edit_upc/',edit_mnp, name='edit-upc'),
    path('check_photo/',verify_selfie, name='verify-selfie'),
    path('release_sim/', release_sim, name='release-sim'),
    path('get_postpaid_plans/', get_postpaid_plans, name='postpaid-plans'),
    path('heartbeat/', heartbeat, name='heartbeat'),
    ### dkyc urls
    path('dkyc_insert/', create_dkyc_record, name='dkyc-post'),
    path('dkyc_sms_send/', dkyc_send_otp, name='dkyc-otp-send'),
    path('dkyc_otp_verify/', dkyc_verify_otp,name='dkyc-otp-verify'),
    path('dkyc_otp_resend/', dkyc_resend_otp,name='dkyc-otp-resend'),
    ### sim upg
    path('sim_upg_otp/', upgradation_send_otp, name='sim-upg-otp'),
    path('sim_upg_otp_verify/', upgradation_verify_otp, name='sim-upg-otp-verify'),
    path('sim_upg_otp_resend/', upgradation_resend_otp, name='sim-upg-otp-resend'),
    ######## mobile no dedup
    path('cafcheck/', check_gsm_caf , name='check-gsm-caf'),
    
    path('checkadh/', check_aadhaar_onboarding , name='check-adhaar'),
    ########### gsm no search 
    
    path('filter_gsmno/', search_gsm_numbers , name='filter-gsmno'),

    ####### gsm no reservation
    path('reserve_gsmno/', reserve_gsm_number , name='reserve-gsmno'),
    path('reserve_gsmno_list/', get_reserved_gsm_numbers , name='get-reserveno-list'),
    ############ sim upgrade
    path('get_customer_info/', get_customer_info , name='get-customer-info'),
    path('sim_upgrade/', create_sim_upgrade_request , name='sim-upgrade'),
    path('get_sim_upgrade_options/', get_app_upgrade_options, name='get-sim-upgrade-options'),
    path('sim_upgrade_report/', list_sim_upgrade_requests, name='list-sim-upgrade-requests'),
    
    ############ esim
    path('esim_test/', get_esim_by_simnumber, name='test_esim'),
    path('esim_caf_submit/',update_caf_details_esim,name='esim-caf-submit'),
    path('esim_otp_send/', send_email_otp, name='esim-otp-send'),
    path('esim_otp_verify/', email_verify_otp,name='esim-otp-verify'),
    path('esim_otp_resend/', email_resend_otp,name='esim-otp-resend'),


    path('get_prepaid_test/', get_prepaid_test, name='get-prepaid-test'),

    ############## CUG
    path('get_business_groups/',search_bulk_business_groups, name='search_business_group'),
    path('get_business_group_details/', get_business_group_details, name='get-group-details' ),

    ############ Pre2post
    path('post_paid_check/',post_to_pre_check, name='search_post_check'),

    ################### sms
    path('send_otp/',app_send_otp, name='app-sms-send'),
    path('verify_otp/',app_verify_otp, name='app-verify-otp'),

    ########### reverification
    
    path('reverify_lookup/',reverify_lookup, name='check_reverification'),
          
]