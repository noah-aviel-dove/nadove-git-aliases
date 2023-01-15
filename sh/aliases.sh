# Prevent accidentally running the script from executing any commands
exit 0;
### b
target=${1:-@};
name=$(git rev --abbrev-ref $target);
echo ${name:-$(git rev $target)}
### rev
if ! default=$(git config --get init.defaultBranch); then
  echo No default branch configured;
  exit 1;
fi;
function repl() { perl -pe "s/(?<!-|\w)$1(?!-|\w)/$2/g"; };
target=$(echo ${@:-@} | repl '-' '@\{-1}' | repl '=' "$default");
git rev-parse $target
### rev8
c8 $(git rev $@)
### l
target=$(git b "$1");
shift;
git log --oneline $target $@;
### hb
git lb $@ --pretty=%h;
### p
git push --dry-run $@ && git push --quiet $@;
### blg
git bl | grep "$1"
### bllg
git bll | grep "$1"
### blrg
git blr | grep "$1"
### co
target=$(git b $1);
shift;
git checkout $target $@
### hr
# Log sha1 of default-descended commit's descendants
git hb = | while read r; do
    if [ "$r" == "$1" ]; then
        break;
    fi;
    echo $r;
done;
### lb
args="$(local_py_exec take_positional_args.py 1 $@)";
head=$(head -1 <<<"$args");
tail=$(tail +2 <<<"$args");
head=$(git b "${head:-=}");
git l $head.. $tail;
### cobig0
# Grep for and checkout branch
function g {
    branch=$(sed 's/^[ *]*//' <<<$1);
    if [[ "$branch" =~ ^remotes/  ]]; then
        branch="--track ${branch%remotes/}";
    fi;
    git co $branch;
};

n=$(wc -l <<<$"$1");
if [[ "$1" =~ ^[[:space:]]*$ ]]; then
    echo No matches;
    return 1;
elif [ $n == 1 ]; then
    g $1;
else
    export -f g;
    run_with_choice g "$1";
fi;
### cobig
git cobig0 "$(git bl | grep $1)";
### coblig
git cobig0 "$(git bll | grep $1)";
### cobrig
git cobig0 "$(git blr | grep $1)";
## corig
# Grep for and checkout revision on current default-descended branch
commits=$(git lb | grep "$1");
function g { git co $(c8 "$1")};
export -f g;
run_with_choice g "$"
### rhq
# Unify `reset --hard <rev>` and `checkout <rev> -- <path>`
if grep -qPe "^-- " <<<"$@"; then
    git co @ $@;
elif grep -qPe " -- " <<<"$@"; then
    git co $@;
else
    git r --hard $@;
fi;
### rh
git d;
git rhq;
### rb
args="$(local_py_exec take_positional_args.py 1 $@)";
head=$(head -1 <<<"$args");
tail=$(tail +2 <<<"$args");
git rebase $(git rev ${head:-=}) $tail;
### aurbc
git au;
git rbc;
### d
args="$(local_py_exec take_positional_args.py 1 $@)";
head=$(head -1 <<<"$args");
tail=$(tail +2 <<<"$args");
git diff $(git rev ${head:-@} $tail);
### d0
git d --exit-code >/dev/null;
### dr
args="$(local_py_exec take_positional_args.py 1 $@)";
head=$(head -1 <<<"$args");
tail=$(tail +2 <<<"$args");
git show --oneline $(git rev ${head:-@} $tail);
### drib
# Explore commits on current default-descended branch
clear -x;
redirects=$(
    for r in $(git hb $1 | tac); do
        echo -n '<(git show --color=always' $r ') ';
    done;
);
bash -c "less -Rf $redirects";
### drig
# Grep for and show commit on current default-descended branch
function g () { git dr $(c8 "$1"); };
run_with_choice g "$(git lb | grep "$1")";
### drlig
# Grep for and list changed files of commit on current default descended branch
function g () { git drl $(c8 "$1"); };
run_with_choice g "$(git lb | grep "$1")";
### cafi
# Amend HEAD to fixup! a commit on the current default-descended branch
function g {
    git caf $1;
};
export -f g;
run_with_choice g "$(git lb)";
### auca
git au;
git ca;
### aucam
git au;
git cam $@;
### aucami
git au;
git cami $@;
### cf
# Commit changes to fixup! the most recent non-fixup! commit on the current default-descended branch
target=$(git lb | grep -vP '^\\w+ fixup!' | head -1);
commit=$(c8 "$target");
msg=$(cut -c10- <<<"$target");
echo fixup! $msg;
git cfr $commit $@;
### cfri
# Commit changes to fixup! a selected commit on the current default-descended branch
commits=$(git lb);
function g { git cfr $(word1 "$1"); };
run_with_choice g "$commits";
### car0
# Precondition check for car(i)
if git ds --exit-code >/dev/null; then
    >&2 echo No changes staged;
    return 1;
elif ! git dd --exit-code >/dev/null; then
    >&2 echo Cannot rebase: there are unstaged changes;
    return 1;
fi;
### car
# Amend a commit on the current default-descended branch with staged changes
git car0 || return 1;
target=$(git rev8 $1);
ESC=$(python -c 'print(chr(0x1b))');
fixup=__FIXUP__;
git ds;
git cm "${fixup}";
vcmds=$(printf "/${fixup}\ndd/${target}\np0dwif ${ESC}:wq");
git rbi <<<"${vcmds}" || git r @~;
### cari
# Select and amend a commit on the current default-descended branch with staged changes
git car0 || return 1;
function g {
    git car $(word1 "$1");
};
export -f g;
run_with_choice g "$(git lb)";
### pu
git p --set-upstream $1 $(git b);
### rhp
# Chained push
for ref in $@; do
    git rh $ref;
    git p;
done;
### rhpf
# Hard reset followed by force push
git rh $1;
git pf;
### rhpfc
# Hard reset followed by force push followed by chained push
refs=$(git hr $1 | tac);
git rhpf $(head -1 <<<"$refs");
git rhp $(tail -n +2 <<<"$refs");
### rhpfci
# Hard reset to selection followed by force push followed by chained push
function g {
    git rhpfc $(word1 "$1");
};
export -f g;
run_with_choice g "$(git lb)";
### fs
git f;
git s;
### frhu
git f;
git rhu;
### END
