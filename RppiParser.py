import json, os

###############################################################################
def ParseIndex(jsonfile, cat="", recipes=[]):
    file_path = os.path.expanduser(jsonfile)
    with open(file_path, "r", encoding='utf-8') as f:
        file_dir = os.path.dirname(file_path)
        cc = ""
        l = file_dir.split('/')
        if len(l) > 0:
            if cat != "":
                cc = cat + '/' + l[-1]
            else:
                cc = cat + l[-1]
        data = json.load(f)
        if 'categories' in data:
            for c in data['categories']:
                file = file_dir + '/' + c['key'] + '/index.json'
                recipes = ParseIndex(file, cc, recipes)
        elif 'recipes' in data:
            for r in data['recipes']:
                r['categories'] =  '/'.join(cc.split('/')[1:])
                if r not in recipes:
                    recipes.append(r)
        f.close()
    return recipes

def FilterRecipe(recipes, key='', value=''):
    if value == '':
        return recipes
    rcps = []
    for r in recipes:
        if key != '':
            if value in r[key]:
                rcps.append(r)
        else:
            for k,v in r.items():
                if value in v and r not in rcps:
                    rcps.append(r)
    return rcps

# from a recipe get all dependencies include itself
def GetAllRecipesDependences(recipe):
    deps = [recipe['repo']]
    try:
        for dep in recipe['dependencies']:
            deps.append(dep)
    except:
        pass
    return deps
