class Match:
    def __init__(self, match_name, match_time):
        self.match_name = match_name
        self.match_time = match_time
        self.options = []
        
    def add_option(self, name, link):
        self.options.append({"name": name, "link": link})