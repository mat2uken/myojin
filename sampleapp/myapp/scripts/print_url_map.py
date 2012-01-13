from kanda import app

def main():
    for rule in app.url_map._rules:
        print '%s => %s' % (rule, rule.endpoint)

