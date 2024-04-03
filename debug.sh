#"program": "/mnt/c/Users/Adam/Documents/Github/downward-dynamic-explore/builds/debug/bin/downward",
#            "args": ["--evaluator", "hff1=ff()", "--evaluator", "hff2=ff()", "--evaluator", "hcea=cea()", "--search", "eager(alt([single(hff1), single(hff2), single(hcea)], boost=0, decision=1), preferred=[])", "--internal-plan-file", "sas_plan"],
#convert above to a single bash command

# Path: debug.sh
/mnt/c/Users/Adam/Documents/Github/downward-dynamic-explore/builds/debug/bin/downward \
    --evaluator "hff1=ff()" \
    --evaluator "hff2=ff()" \
    --evaluator "hcea=cea()" \
    --search "eager(alt([single(hff1), single(hff2), single(hcea)], boost=0, decision=1), preferred=[])" \
    --internal-plan-file "sas_plan" \
    < output.sas