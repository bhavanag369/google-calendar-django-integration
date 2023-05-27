import os
from django.shortcuts import redirect
from rest_framework.decorators import api_view
from rest_framework.response import Response
import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery

CLIENT_SECRETS_FILE = \
    "client_secret_1003679408995-bcsim5h5mhvcn5jmfmh86jisq0vq0epg.apps.googleusercontent.com.json"

SCOPES = ['https://www.googleapis.com/auth/calendar',
          'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile',
          'openid']
REDIRECT_URL = 'http://127.0.0.1:8000/convinchallenge/v1/calendar/redirect'
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v1'


@api_view(['GET'])
def GoogleCalendarInitView(request):
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URL

        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true')
        print("authorization_url => ", authorization_url)
        print("state => ", state)

        request.session['mystate'] = state
        request.session.save()
        print("request => ", request)

        return Response({"authorization_url": authorization_url})
    except Exception as err:
        print("**ERROR**", err)

def convert_creds_to_json(credentials):
  return {
      'token': credentials.token,
      'refresh_token': credentials.refresh_token,
      'token_uri': credentials.token_uri,
      'client_id': credentials.client_id,
      'client_secret': credentials.client_secret,
      'scopes': credentials.scopes
  }

@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    try:
        print("here")
        print("creds", request.session.get('credentials'))
        state = request.session['mystate']
        print("state => ", state)

        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
        flow.redirect_uri = REDIRECT_URL

        authorization_response = request.get_full_path()
        print("authorization_response => ", authorization_response)
        flow.fetch_token(authorization_response=authorization_response)
        print("flow => ", flow)

        credentials = flow.credentials
        print("credentials => ", credentials)
        request.session['credentials'] = convert_creds_to_json(credentials)

        if 'credentials' not in request.session:
            return redirect('v1/calendar/init')

        credentials = google.oauth2.credentials.Credentials(
            **request.session['credentials'])
        print("credentials => ", credentials)

        service = googleapiclient.discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=credentials)

        calendar_list = service.calendarList().list().execute()

        calendar_id = calendar_list['items'][0]['id']

        events  = service.events().list(calendarId=calendar_id).execute()

        events_list_append = []
        if not events['items']:
            print('No data found.')
            return Response({"message": "No data found or user credentials invalid."})
        else:
            for events_list in events['items']:
                events_list_append.append(events_list)
                return Response({"events": events_list_append})
        return Response({"error": "calendar event aren't here"})
    except Exception as err:
        print("**ERROR**", err)
