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
                                  lambda props, prop: True if populate_list_property_with_trophy_titles(
                                      game_list) else True)

    trophy_list = obs.obs_properties_add_list(props,
                                              'trophy_list',
                                              'Trophies',
                                              obs.OBS_COMBO_TYPE_LIST,
                                              obs.OBS_COMBO_FORMAT_STRING)

    obs.obs_property_set_modified_callback(trophy_list, trophy_list_callback)

    obs.obs_properties_add_button(props, 'get_trophies', 'Get Trophies',
                                  lambda props, prop: True if populate_list_property_with_trophies_for_title(
                                      trophy_list) else True)

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
    global token, trophy_titles
    trophy_titles = psn.get_trophy_titles(token)
    obs.obs_property_list_clear(list_property)
    obs.obs_property_list_add_string(list_property, '', '')
    for trophy_title in trophy_titles['trophyTitles']:
        trophy_title_name = f'{trophy_title["trophyTitleName"]} ({trophy_title["trophyTitlePlatform"]})'
        trophy_title_npCommunicationId = trophy_title["npCommunicationId"]
        obs.obs_property_list_add_string(list_property, trophy_title_name, trophy_title_npCommunicationId)
    return True


def populate_list_property_with_trophies_for_title(list_property):
    global token, trophy_title, trophies

    obs.obs_property_list_clear(list_property)
    obs.obs_property_list_add_string(list_property, '', '')
    trophies = psn.get_trophies_for_title(token, trophy_title)
    earned_trophies = psn.get_trophies_earned_for_title(token, trophy_title)

    for trophy in trophies['trophies']:
        trophy_earned = earned_trophies['trophies'][trophy['trophyId']]['earned']
        if not trophy_earned:
            trophy_name = trophy['trophyName']
            trophy_desc = trophy['trophyDetail']
            # trophy_icon = trophy['trophyIconUrl']
            # May need to cast this back since it is a numeric min 0 type in psn api documentation
            trophy_id = str(trophy['trophyId'])
            obs.obs_property_list_add_string(list_property, f'{trophy_name}: {trophy_desc}', trophy_id)

    return True


def npsso_text_callback(props, prop, settings):
    print('npsso_text_callback')
    global npsso
    print(obs.obs_data_get_string(settings, 'npsso'))
    npsso = obs.obs_data_get_string(settings, 'npsso')
    return True


def game_list_callback(props, prop, settings):
    print('game_list_callback')
    # On refresh, set the trophyTitle correctly.
    global trophy_titles, trophy_title
    refresh = False

    # Search the trophyTitles list for the trophyTitle dict that we want.
    npCommunicationId = obs.obs_data_get_string(settings, 'game_list')
    if trophy_titles:
        for temp_trophy_title in trophy_titles['trophyTitles']:
            if npCommunicationId == temp_trophy_title['npCommunicationId']:
                trophy_title = temp_trophy_title

    return refresh


def trophy_list_callback(props, prop, settings):
    print('trophy_list_callback')
