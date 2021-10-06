import psn
import obspython as obs

token = ''
npsso = ''
trophy_titles = {}
trophy_title = {}

def script_defaults(settings):
    global npsso
    npsso = obs.obs_data_get_string(settings, 'npsso')

def script_description():
    return '''<h1>PSN Trophies</h1>
Track trophies for a PSN account.'''

def script_defaults(settings):
    global npsso, token
    obs.obs_data_set_default_string(settings, 'npsso', '')
    obs.obs_data_set_default_string(settings, 'token', '')
    npsso = obs.obs_data_get_string(settings, 'npsso')
    #token = obs.obs_data_get_string(settings, 'token')

def script_properties():
    print('script_properties')
    global token
    props = obs.obs_properties_create()
    obs.obs_properties_add_text(props, 'npsso', 'npsso', obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_button(props, 'get_token', 'Get Token', get_token)
    #obs.obs_properties_add_text(props, 'token', 'token', obs.OBS_TEXT_DEFAULT)
    game_list = obs.obs_properties_add_list(props,
                                            'game_list',
                                            'Games',
                                            obs.OBS_COMBO_TYPE_LIST,
                                            obs.OBS_COMBO_FORMAT_STRING)
    print(f'Token: {token}')
    if token:
        populate_list_property_with_trophy_titles(game_list)
    obs.obs_properties_add_button(props, 'get_trophy_titles', 'Get Game List',
        lambda props, prop: True if populate_list_property_with_trophy_titles(game_list) else True)
    obs.obs_properties_add_button(props, 'get_trophies_for_title', 'Get Trophies List',
        lambda props, prop: True if populate_checklist_properties_with_trophy_list_for_title(props) else True)
    
    return props

def script_update(settings):
    print('script_update')
    global npsso
    global token
    global trophy_titles
    global trophy_title
    npsso = obs.obs_data_get_string(settings, 'npsso')
    npCommunicationId = obs.obs_data_get_string(settings, 'game_list')
    for temp_trophy_title in trophy_titles['trophyTitles']:
        if npCommunicationId == temp_trophy_title['npCommunicationId']:
            trophy_title = temp_trophy_title

def get_token(props, property):
    global token
    token = psn.get_psn_token(npsso)
    return True

def populate_list_property_with_trophy_titles(list_property):
    global token
    global trophy_titles
    trophy_titles = psn.get_trophy_titles(token)
    obs.obs_property_list_clear(list_property)
    obs.obs_property_list_add_string(list_property, '', '')
    for trophy_title in trophy_titles['trophyTitles']:
        trophy_title_name = f'{trophy_title["trophyTitleName"]} ({trophy_title["trophyTitlePlatform"]})'
        trophy_title_npCommunicationId = trophy_title["npCommunicationId"]
        obs.obs_property_list_add_string(list_property, trophy_title_name, trophy_title_npCommunicationId)

def populate_checklist_properties_with_trophy_list_for_title(props):
    global token, trophy_title
    trophies = psn.get_trophies_for_title(token, trophy_title)
    earned_trophies = psn.get_trophies_earned_for_title(token, trophy_title)
    for trophy in trophies['trophies']:
        trophy_earned = earned_trophies['trophies'][trophy['trophyId']]['earned']
        prop = obs.obs_properties_add_bool(props, str(trophy["trophyId"]), trophy['trophyName'])
        if trophy_earned:
            obs.obs_property_set_enabled(prop, False)
        
