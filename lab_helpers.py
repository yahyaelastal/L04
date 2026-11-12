"""Helper functions for  L04"""
import importlib
import inspect
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

S = {}  # lab state: user, token, model, tokenizer


def sh(cmd, cwd=None):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return (r.stdout + r.stderr).strip()


def check(label, ok, hint=""):
    print(("[OK]   " if ok else "[FAIL] ") + label + ("" if ok or not hint else f"\n       Hint: {hint}"))
    return ok


# ---------------------------------------------------------------- setup

def setup(user, token):
    S.update(user=user, token=token)
    req = urllib.request.Request("https://api.github.com/user",
                                 headers={"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req) as r:
            me = json.loads(r.read())
    except urllib.error.HTTPError:
        me = {}
    if check("token works", me.get("login", "").lower() == user.lower(), "check the GH_TOKEN secret and your username"):
        sh(f'git config user.name "{me["login"]}"')
        sh(f'git config user.email "{me["id"]}+{me["login"]}@users.noreply.github.com"')


def load_model(name="Qwen/Qwen3-4B-Instruct-2507"):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    S["tok"] = AutoTokenizer.from_pretrained(name)
    S["model"] = AutoModelForCausalLM.from_pretrained(name, torch_dtype=torch.float16, device_map="auto")
    print("[OK]   model loaded")


def ask(skill_text, user_text, max_new_tokens=800):
    tok, model = S["tok"], S["model"]
    messages = [{"role": "system", "content": skill_text}, {"role": "user", "content": user_text}]
    enc = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt",
                                  return_dict=True).to(model.device)
    out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False)
    return tok.decode(out[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)


def skill(name):
    """The text of a skill, without its --- header."""
    text = open(f"skills/{name}/SKILL.md").read()
    if "PASTE YOUR" in text:
        print(f"[FAIL] skills/{name}/SKILL.md only contains the placeholder text: you ran the cell without pasting your skill.\n"
              f"       Hint: get back the version from your last commit with: !git checkout skills/{name}/SKILL.md")
    return text.split("---", 2)[-1].strip()


# ---------------------------------------------------------------- skill 1: bug reports

def split_reports(text):
    parts = re.split(r"(?=^\s*Line:\s*\d+)", text, flags=re.M)
    return [p.strip() for p in parts if re.match(r"\s*Line:\s*\d+", p)]


def find_bugs(file):
    """Runs your bug-finder skill on one exercise file and saves the reports in reports/."""
    code = open(file).read()
    numbered = "\n".join(f"{i:3d} | {l}" for i, l in enumerate(code.splitlines(), 1))
    reports = split_reports(ask(skill("bug-finder"), numbered))
    name = file.replace(".py", "")
    with open(f"reports/{name}.md", "w") as f:
        f.write(f"# Bug reports for {file}\n\n" + "\n\n".join(reports) + "\n")
    for k, r in enumerate(reports, 1):
        print(f"---------------- bug report {k}\n{r}\n")
    return check(f"{len(reports)} bug reports saved in reports/{name}.md", len(reports) > 0,
                 "no report in the right format: check that your skill asks for Line: / Problem: / Example: / Fix:")


# ---------------------------------------------------------------- skill 2: tests

def clean_code(text):
    m = re.search(r"`{3}(?:python)?\n(.*?)`{3}", text, re.S)
    code = (m.group(1) if m else text).strip()
    return "\n".join(l for l in code.splitlines() if not re.match(r"\s*(from\s+\w*exercise\w*\s+import|import\s+\w*exercise)", l))


def write_tests(file):
    """Runs your test-writer skill on each bug report and saves the tests in tests/."""
    name = file.replace(".py", "")
    path = f"reports/{name}.md"
    if not os.path.exists(path):
        return check("bug reports found", False, f'run find_bugs("{file}") first')
    code = open(file).read()
    reports = split_reports(open(path).read())
    tests = []
    for k, r in enumerate(reports, 1):
        t = clean_code(ask(skill("test-writer"), f"## Bug report\n{r}\n\n## The file {file}\n{code}", max_new_tokens=400))
        t = re.sub(r"def test_", f"def test_r{k}_", t)          # unique names, one group per report
        tests.append(f"# bug report {k}\n{t}")
        print(f"---------------- test for bug report {k}\n{t}\n")
    with open(f"tests/test_{name}.py", "w") as f:
        f.write(f"import os\nimport sqlite3\nimport subprocess\n\nimport pytest\n\nimport {name}\nfrom {name} import *\n\n\n" + "\n\n\n".join(tests) + "\n")
    return check(f"{len(tests)} tests saved in tests/test_{name}.py", len(tests) > 0)


def run_tests(file):
    """Runs the tests of one exercise file and shows which pass and which fail."""
    name = file.replace(".py", "")
    out = sh(f"python -m pytest tests/test_{name}.py -q -rA --no-header -p no:cacheprovider")
    for line in out.splitlines():
        if line.startswith(("PASSED", "FAILED", "ERROR")):
            status, test = line.split(" ", 1)
            print(("PASS  " if status == "PASSED" else "FAIL  ") + test.split("::")[-1].split(" - ")[0])
    print("\n" + (out.splitlines()[-1] if out else "no output"))


# ---------------------------------------------------------------- the teacher's checks

def _load(file, code=None):
    """Imports an exercise file (or the given code) as a fresh module."""
    name = file.replace(".py", "")
    if code is None:
        sys.modules.pop(name, None)
        return importlib.import_module(name)
    import types
    mod = types.ModuleType(name)
    exec(code, mod.__dict__)
    return mod


def _ok(f):
    try:
        return bool(f())
    except Exception:
        return False


def _db():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE users (username TEXT, email TEXT)")
    db.execute("INSERT INTO users VALUES ('ana', 'ana@mail.com')")
    return db


CHECKS = {
    "exercise1.py": {
        "is_even": lambda m: m.is_even(4) is True and m.is_even(7) is False,
        "rectangle_area": lambda m: m.rectangle_area(3, 4) == 12,
        "double": lambda m: m.double(5) == 10 and m.double(0) == 0,
    },
    "exercise2.py": {
        "is_passing": lambda m: m.is_passing(5) is True and m.is_passing(4) is False,
        "is_valid_password": lambda m: m.is_valid_password("abcdefg1") and not m.is_valid_password("abcdefgh"),
        "clamp": lambda m: m.clamp(15, 0, 10) == 10 and m.clamp(-5, 0, 10) == 0 and m.clamp(5, 0, 10) == 5,
    },
    "exercise3.py": {
        "average": lambda m: m.average([]) == 0 and m.average([4, 5]) == 4.5,
        "first_word": lambda m: m.first_word("") == "" and m.first_word("hello world") == "hello",
        "percent": lambda m: m.percent(1, 0) == 0 and m.percent(1, 4) == 25,
    },
    "exercise4.py": {
        "ADMIN_PASSWORD": lambda m: "admin123" not in inspect.getsource(m),
        "find_user": lambda m: m.find_user(_db(), "x' OR '1'='1") is None and m.find_user(_db(), "ana") is not None,

    },
}


def check_round(n):
    """The final check of an exercise: are all bugs fixed, are your tests good, is your work pushed?"""
    file = f"exercise{n}.py"
    name = f"exercise{n}"
    print(f"Exercise {n}: {file}\n")
    try:
        mod = _load(file)
    except Exception as e:
        return check(f"{file} runs", False, f"{type(e).__name__}: {e}")
    fixed = 0
    for fn, test in CHECKS[file].items():
        ok = _ok(lambda: test(mod))
        fixed += ok
        check(f"{fn} fixed", ok, "this bug is still there")

    # good tests: they fail on the original code and pass on yours
    good = total = 0
    if os.path.exists(f"tests/test_{name}.py"):
        first = sh("git rev-list --max-parents=0 HEAD").split()[0]
        with tempfile.TemporaryDirectory() as tmp:
            sh(f"cp -r tests {tmp}/")
            with open(f"{tmp}/{file}", "w") as f:
                f.write(sh(f"git show {first}:{file}"))
            before = sh(f"python -m pytest tests/test_{name}.py -q -rA --no-header -p no:cacheprovider", cwd=tmp)
        after = sh(f"python -m pytest tests/test_{name}.py -q -rA --no-header -p no:cacheprovider")
        status = lambda out: {l.split(" ", 1)[1].split(" - ")[0]: l.split(" ", 1)[0] for l in out.splitlines()
                              if l.startswith(("PASSED", "FAILED", "ERROR"))}
        b, a = status(before), status(after)
        total = len(a)
        good = sum(1 for t in a if a[t] == "PASSED" and b.get(t) in ("FAILED", "ERROR"))
    print()
    check(f"good tests: {good}/{total} (fail on the original code, pass on yours)", total > 0 and good == total,
          "a test that passes on the original code does not prove anything")

    branch = sh("git branch --show-current")
    pushed = (branch == f"fix/{name}" and branch in sh("git ls-remote --heads origin")
              and not sh(f"git log origin/{branch}..HEAD --oneline"))
    check(f"branch fix/{name} pushed to GitHub", pushed, "commit, then run: !git push -u origin HEAD")
    print(f"\nBugs fixed: {fixed}/{len(CHECKS[file])}")
    return fixed == len(CHECKS[file]) and pushed
