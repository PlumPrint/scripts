import os
from sys import stderr

def send_slack_message(x):
    import requests
    url = "".join([
        "https://plumprint.slack.com/services/hooks/",
        "slackbot?token=MrTl0qeToohOxQsCxAvXIXYA&channel=%23editing"
    ])
    requests.post(url, data = x)

# :: Workflow -> Count
def read_sheet():
    import re
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "bookstarts-dc2075e7bba3.json", 
        ["https://spreadsheets.google.com/feeds"]
    )
    gc = gspread.authorize(credentials)
    gs = gc.open("Image Editing").sheet1
    xs = gs.get_all_values()
    ys = {}
    for x in xs:
        y = re.search(r"30[0-9]{4}", x[1])
        if not y:
            continue
        if not x[6]:
            ys[y.group()] = -1
            continue
        try:
            z = ys.get(y.group(), 0)
            if z == -1:
                continue
            ys[y.group()] = z + int(x[3])
        except Exception as e:
            print >> stderr, y.group(), e
            continue
    return ys

# :: Workflow -> ()
def credit_workflow(workflow):
    import re
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "bookstarts-dc2075e7bba3.json", 
        ["https://spreadsheets.google.com/feeds"]
    )
    gc = gspread.authorize(credentials)
    gs = gc.open("Image Editing").sheet1
    
    ks = dict(zip(gs.row_values(1)[8:14], range(9, 15)))
    xs = gs.findall(re.compile(r"%s_" % workflow))
    for x in xs:
        n = gs.cell(x.row, 4).value
        k = gs.cell(x.row, 5).value.strip()
        gs.update_cell(x.row, ks[k], n)

# :: Workflow -> [Dirname]
def find_upload(workflow):
    import glob
    xs = glob.glob(
        "/Volumes/Dropbox/_FREELANCERS/editors/*-*/*%s*" % (
        workflow
    ))
    if not xs:
        raise Exception(
            "%s edited folder not found" % workflow
        )
    if len(set(
        os.path.basename(x).split("_Folder")[0] for x in xs
    )) > 1:
        raise Exception(
            "%s multiple edited folders %s" % (workflow, xs)
        )
    return sorted(xs, key = os.path.basename)
    
# :: [Dirname] -> Count
def image_count(xs):
    n = 0
    for x in xs:
        for y in os.listdir(x):
            if os.path.isdir(y):
                raise Exception(
                    "%s has a subfolder (%s)" % (x, y)
                )
            if y[-4:].lower() in [".jpg", ".tif"]:
                n += 1
    return n

# :: Workflow -> Count
def asf_image_count(workflow):
    import requests
    y = requests.get(
        "https://www.plumprint.com/workflow/get-asf/",
        params = {"workflow": workflow}
    ).json()
    if not y:
        raise Exception(
            "%s no ASF in admin" % workflow
        )
    return y["pieces"]
   
# :: [Workflow]
def workflows_in_edit():
    import requests
    return requests.get(
        "https://www.plumprint.com/workflow/in-edit/"
    ).json()
    
def merge_dirs(a, b):
    for x in os.listdir(a):
        p = os.path.join(a, x)
        if not os.path.isfile(p):
            raise Exception(
                "%s is not a file" % p
            )
        q = os.path.join(b, x)
        if os.path.exists(q):
            raise Exception(
                "%s exists in %s" % (p, q)
            )
        #print "mv %s %s" % (p, q)
        os.rename(p, q)
    os.rmdir(a)

# :: [Dirname] -> ()
def move_images(xs):
    if len(xs) == 1:
        y = "/Volumes/Dropbox/Edits to Review/%s" % (
            os.path.basename(xs[0])
        )
        os.rename(xs[0], y)
        return y
    n = image_count(xs)
    for x, y in zip(xs, xs[1:]):
        merge_dirs(x, y)
    z = "%s (%s)" % (
        xs[-1].split("_Folder%s" % len(xs))[0],
        n
    )
    os.rename(xs[-1], z)
    return move_images([z])
    
def start_book(workflow):
    import requests
    f = read_sheet()
    n = f.get(workflow)
    if not n:
        return
        raise Exception(
            "%s is in edit but not on sheet" % workflow
        )
    if n == -1:
        return
        raise Exception(
            "%s is not finished" % workflow
        )
    x = find_upload(workflow)
    p = image_count(x)
    q = asf_image_count(workflow)
    if p != q:
        raise Exception(
            "%s has %s images, should have %s (%s)" % (
                workflow,
                p,
                q,
                x
            )
        )
    # print workflow
    # return
    #
    y = move_images(x)
    # print workflow, y
    print "done", workflow
    
    # print "\nmv %s %s" % (x, move_images(x))
    requests.post(
        "https://www.plumprint.com/workflow/new-layout-job/",
        data = {"workflow": workflow}
    )
    credit_workflow(workflow)
    credit_workflow(workflow)
    return

def start_books():
    for x in workflows_in_edit():
    # for x in ["300074"]:
    # for x in ["300074"]:
        try:
            # print "start_book", x
            start_book(x)
        except Exception as e:
            send_slack_message(str(e))
            print >> stderr, x, e

start_books()
# print asf_image_count("305501")
# credit_workflow("400000")
# send_slack_message("test")
