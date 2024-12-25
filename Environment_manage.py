import configparser
import os

class EnvironmentManager:
    def __init__(self, ini_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.ini = ini_file
        if not os.path.exists(self.ini):
            self._update()
        self.config.read(self.ini)
    
    def get_all_section_names(self):
        return self.config.sections()
    
    def get_all_user(self):
        sections = self.get_all_section_names()
        if "CUR_USER" in sections:
           sections.remove("CUR_USER")
        return sections

    def get_section(self, section_name) -> dict:
        if section_name in self.config.sections():
            return dict(self.config[section_name])
        return dict()
    
    def get_section_keys(self, section_name) -> list:
        return list(self.config[section_name].keys())

    def add_section(self, section_name, evironment):
        if section_name not in self.config.sections():
            self.config.add_section(section_name)
        if isinstance(evironment, dict):
            for key, value in evironment.items():
                self.config[section_name][key] = value
        elif isinstance(evironment, list) or isinstance(evironment, tuple):
            keys = self.get_section_keys(self.get_all_section_names()[0])
            if len(keys) != len(evironment):
                raise ValueError("환경변수 개수가 일치하지 않습니다.")
            for key, value in zip(keys, evironment):
                self.config[section_name][key] = value
        self._update()

    def remove_section(self, section_name):
        if section_name in self.config.sections():
            self.config.remove_section(section_name)
        self._update()

    def get_current_user(self):
        sections = self.get_all_section_names()
        if "CUR_USER" in sections:
            return self.config['CUR_USER'].get('USER')  
        users = self.get_all_user()
        if users:
            self.add_section(section_name='CUR_USER', evironment={'USER': users[0]})
            return users[0]
        return None

    def set_current_user(self, user):
        self.config['CUR_USER']['USER'] = user 
        self._update() 
    
    def clear_environment(self):
        self.config.clear()
        self._update()
    
    def _update(self):
        with open(self.ini, 'w') as configfile:
            self.config.write(configfile)
        return
    
if __name__ == '__main__':
    env = EnvironmentManager()
    env.add_section('CUR_USER', {'USER': 'PASSWORD'})
    print(env.get_current_user())