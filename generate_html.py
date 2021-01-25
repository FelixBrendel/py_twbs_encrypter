import shutil
import os
import random
import string
import subprocess
import re
import sys
import pyaes

if len(sys.argv) != 4:
    print("Usage: python3 generate_html.py org_dir output_dir master_key")
    sys.exit(1)

org_dir, output_dir, master_key = sys.argv[1:]

if len(master_key) not in [16, 24, 32]:
    print(f"Usage: master_key must be either 16, 24 or 32 bytes long (was {len(master_key)})")
    sys.exit(1)

master_key = master_key.encode("utf-8")
author = "Felix Brendel"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

org_files = []
keys = []
titles = []

for filename in sorted(os.listdir(org_dir)):
    if filename.endswith(".org"):
        org_files.append(filename[:-4])

        with open(os.path.join(org_dir, filename), "r") as org_file:
            text = org_file.read()
            match = re.search(r"#\+title: (.*)", text, re.IGNORECASE)
            if match:
                titles.append(match.group(1))
            else:
                titles.append("no title")

            match = re.search(r"#\+aes_key: (.*)", text, re.IGNORECASE)
            if match:
                keys.append(match.group(1).encode("utf-8"))
            else:
                keys.append(None)

# TODO(Felix): do the (require 'org) in the emacs config in the docker
export_command = """
  (save-window-excursion
    (require 'org)
    (setq org-publish-project-alist
      '(("project"
         :base-directory "{}"
         :publishing-directory "{}"
         :publishing-function org-twbs-publish-to-html
         :with-sub-superscript nil)))
    (setq user-full-name    "{}")
    (org-publish-all t))
    """.replace("\n", " ")


abs_org_dir = os.path.abspath(org_dir)
cmd = f'{export_command.format(abs_org_dir, abs_org_dir, author)}'

# if on windows
cmd = cmd.replace("\\", "\\\\")

r = subprocess.call(['emacsclient', "-e", cmd])

if r != 0:
    print("emacs error")
    sys.exit(1)

for org_file, org_key in zip(org_files, keys):
    full_path = os.path.join(org_dir, org_file + ".org")
    generated_file = os.path.join(org_dir, org_file + ".html")

    with open(generated_file, "r") as html:
        text = html.read()
        # insert custon style sheet
        text = text.replace("<head>",
                     """<head>
                     <link href="./styles.css" rel="stylesheet">""")

        # sidebar + logo html string
        sidebar_html = """
                       <body>
                         <div class="side-bar">
                           <a href="./">
                             <img class="logo" src="./images/logo.png"/>
                           </a>
                           <ul class="side-links">
        """
        # insert every page except index into the sidebar
        for other_org_file, title, key in zip(org_files, titles, keys):
            # index should not appear in the list on the left
            if other_org_file == "index":
                continue
            maybe_lock = '' if not key else '\uD83D\uDD10 '
            s = '' if other_org_file != org_file else 'class=\"active\"'
            sidebar_html += f"<li><a {s} href=\"{other_org_file}.html\">{maybe_lock}{title}</a></li>"

        sidebar_html += """ </ul>
                         </div>
        """

        # insert sidebar into the html
        text = text.replace("<body>", sidebar_html)

        if org_key:
            real_key = "".join(random.choice(string.ascii_letters) for i in range(32)).encode("utf-8")

            aes = pyaes.AESModeOfOperationCTR(org_key)
            org_key_enc_real_key = aes.encrypt(real_key).hex()

            aes = pyaes.AESModeOfOperationCTR(master_key)
            master_key_enc_real_key = aes.encrypt(real_key).hex()

            text_list = text.split("<body>")
            assert(len(text_list) == 2)
            header = text_list[0]
            body, footer = text_list[1].split("</body>")
            correct_key_marker = "<!--Correct Key-->"
            body = correct_key_marker + body
            aes = pyaes.AESModeOfOperationCTR(real_key)
            real_key_enc_body = aes.encrypt(body.encode("utf-8")).hex()
            header = header.replace("</head>", f"""
<script type="text/javascript" src="https://cdn.rawgit.com/ricmoo/aes-js/e27b99df/index.js"></script>
<script>
  var enc_hex_body = "{real_key_enc_body}";
  var master_key_enc_real_key = "{master_key_enc_real_key}";
  var org_key_enc_real_key = "{org_key_enc_real_key}";
  var correct_key_marker = "{correct_key_marker}"
</script>
<script type="text/javascript" src="decipher.js"></script>""")
            text = " ".join([header, "<body></body>", footer])


        # write html to new location
        with open(os.path.join(output_dir, org_file + ".html"), "wb") as new_html:
            new_html.write(text.encode("utf-8"))

    # delete old file
    os.remove(generated_file)

# copy other needed files
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "decipher.js"), os.path.join(output_dir, "decipher.js"))
shutil.copy(os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles.css"),   os.path.join(output_dir, "styles.css"))

print("done")
