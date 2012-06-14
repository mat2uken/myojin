from flask import current_app as app

def main():
    for rule in app.url_map._rules:
        print '%s => %s' % (rule, rule.endpoint)

