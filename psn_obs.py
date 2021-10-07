import psn
import obspython as obs

token = ''
npsso = ''
trophy_titles = {}
trophy_title = {}
trophies = {}

def script_description():
    return '''<h1>PSN Trophies</h1>
Track trophies for a PSN account.'''

def script_defaults(settings):
    print(f'{obs.obs_data_get_json(settings)}')
    print('script_defaults')
    global npsso, token
#    obs.obs_data_set_default_string(settings, 'npsso', '')
#    obs.obs_data_set_default_string(settings, 'token', '')
    npsso = obs.obs_data_get_string(settings, 'npsso')

def script_properties():
    print('script_properties')
    global token
    props = obs.obs_properties_create()

    npsso_text = obs.obs_properties_add_text(props, 'npsso', 'npsso', obs.OBS_TEXT_PASSWORD)
    obs.obs_property_set_modified_callback(npsso_text, npsso_text_callback)

    obs.obs_properties_add_button(props, 'get_token', 'Get Token', get_token)

    game_list = obs.obs_properties_add_list(props,
                                            'game_list',
                                            'Games',
                                            obs.OBS_COMBO_TYPE_LIST,
                                            obs.OBS_COMBO_FORMAT_STRING)

    obs.obs_property_set_modified_callback(game_list, game_list_callback)

    obs.obs_properties_add_button(props, 'get_trophy_titles', 'Get Game List',
        lambda props, prop: True if populate_list_property_with_trophy_titles(game_list) else True)
    
    return props

def script_update(settings):
    print('script_update')

def get_token(props, property):
    print('get_token')
    global token
    print(npsso)
    token = psn.get_psn_token(npsso)
    print(token)
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
    return True

def populate_checklist_properties_with_trophy_list_for_title(props):
    global token, trophy_title, trophies
    refresh = False
    trophies = psn.get_trophies_for_title(token, trophy_title)
    earned_trophies = psn.get_trophies_earned_for_title(token, trophy_title)
    for trophy in trophies['trophies']:
        refresh = True
        trophy_earned = earned_trophies['trophies'][trophy['trophyId']]['earned']
        prop = obs.obs_properties_add_bool(props, f'{trophy_title["npCommunicationId"]}-{trophy["trophyId"]}', trophy['trophyName'])
        obs.obs_property_set_long_description(prop, trophy['trophyDetail'])
        if trophy_earned:
            obs.obs_property_set_enabled(prop, False)
    return True
        
def clear_checklist_properties(props):
    print('clear_checklist_properties')
    global trophy_title, trophies
    if trophies:
        print('Clearing trophies')
        for trophy in trophies['trophies']:
            obs.obs_properties_remove_by_name(props, f'{trophy_title["npCommunicationId"]}-{trophy["trophyId"]}')
        return True
    else:
        return False

def npsso_text_callback(props, prop, settings):
    print('npsso_text_callback')
    global npsso
    print(obs.obs_data_get_string(settings, 'npsso'))
    npsso = obs.obs_data_get_string(settings, 'npsso')
    return True

def game_list_callback(props, prop, settings):
    print('game_list_callback')
    # On refresh, clear currently existing trophies, set the trophyTitle correctly, and create props for new trophies.
    global trophy_titles, trophy_title
    refresh = False
    refresh = clear_checklist_properties(props)
    # Search the trophyTitles list for the trophyTitle dict that we want.
    npCommunicationId = obs.obs_data_get_string(settings, 'game_list')
    if trophy_titles:
        for temp_trophy_title in trophy_titles['trophyTitles']:
            if npCommunicationId == temp_trophy_title['npCommunicationId']:
                trophy_title = temp_trophy_title
    if trophy_title:
        refresh = populate_checklist_properties_with_trophy_list_for_title(props)
    return refresh
