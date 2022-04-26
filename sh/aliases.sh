# Prevent accidentally running the script from executing any commands
exit 0;
### b
target=$(sed 's/^-$/@{-1}/g'<<<${1:-@});
git rev-parse --abbrev-ref $target
### rev
target=$(sed 's/^-$/@{-1}/g'<<<${1:-@});
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
### hr
# Log sha1 of develop-descended commit's descendants
git hdev | while read r; do
    if [ "$r" == "$1" ]; then
        break;
    fi;
    echo $r;
done;
### lb
parent=$(git b "$1");
shift;
git l $parent.. $@;
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
# Grep for and checkout revision on current develop-descended branch
commits=$(git ldev | grep "$1");
function g { git co $(c8 "$1")};
export -f g;
run_with_choice g "$"
### rh
# Unify `reset --hard <rev>` and `checkout <rev> -- <path>`
if grep -qPe "^-- " <<<"$@"; then
    git co @ $@;
elif grep -qPe " -- " <<<"$@"; then
    git co $@;
else
    git r --hard $@;
fi;
### aurbc
git au;
git rbc;
### d0
git d --exit-code >/dev/null;
### dr
git show --oneline $(git rev "$1");
### dridev
# Explore commits on current develop-descended branch
clear -x;
redirects=$(
    for r in $(git hdev | tac); do
        echo -n '<(git show --color=always' $r ') ';
    done;
);
bash -c "less -Rf $redirects";
### drig
# Grep for and show commit on current develop-descended branch
function g () { git dr $(c8 "$1"); };
run_with_choice g "$(git ldev | grep "$1")";
### drlig
# Grep for and list changed files of commit on current develop-descended branch
function g () { git drl $(c8 "$1"); };
run_with_choice g "$(git ldev | grep "$1")";
### cafi
# Amend HEAD to fixup! a commit on the current develop-descended branch
function g {
    git caf $1;
};
export -f g;
run_with_choice g "$(git ldev)";
### cf
# Commit changes to fixup! the most recent non-fixup! commit on the current develop-descended branch
target=$(git ldev | grep -vP '^\\w+ fixup!' | head -1);
commit=$(c8 "$target");
msg=$(cut -c10- <<<"$target");
echo fixup! $msg;
git cfr $commit $@;
### cfri
# Commit changes to fixup! a selected commit on the current develop-descended branch
commits=$(git ldev);
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
# Amend a commit on the current develop-descended branch with staged changes
git car0 || return 1;
target=$(git rev8 $1);
ESC=$(python -c 'print(chr(0x1b))');
fixup=__FIXUP__;
git ds;
git cm "${fixup}";
vcmds=$(printf "/${fixup}\ndd/${target}\np0dwif ${ESC}:wq");
git rbidev <<<"${vcmds}" || git r @~;
### cari
# Select and amend a commit on the current develop-descended branch with staged changes
git car0 || return 1;
function g {
    git car $(word1 "$1");
};
export -f g;
run_with_choice g "$(git ldev)";
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
run_with_choice g "$(git ldev)";
### fs
git f;
git s;
### frhu
git f;
git rhu;
### END
