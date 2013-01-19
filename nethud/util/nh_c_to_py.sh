#!/bin/sh

NH_SOURCE=$1

OUTPUT_FILE=monst.py
echo -e 'monster_list = [\n    "list is one-indexed",' > $OUTPUT_FILE
grep '^    MON' $NH_SOURCE/libnethack/src/monst.c | awk '{$NF=""}1' | sed -e 's/MON(//g' -e 's/^/    /g' -e 's/ $//g' >> $OUTPUT_FILE
echo -e ']\nmonsters = {' >> $OUTPUT_FILE
grep '^    MON' $NH_SOURCE/libnethack/src/monst.c | sed -e 's/MON(//g' -e 's/, /: "/g' -e 's/,/",/g' >> $OUTPUT_FILE
echo -e '}\nmonster_syms = {' >> $OUTPUT_FILE
grep 'DEF_' $NH_SOURCE/libnethack/include/monsym.h | sed -e 's/DEF_/S_/g' -e 's/# define //g' -e 's/  */": /g' -e 's/^/    "/g' -e 's/$/,/g' >> $OUTPUT_FILE
echo -e '}\ndef lookup_monster(number):\n    monster = monster_list[number]\n    return "{0} ({1})".format(monster_syms[monsters[monster]], monster)' >> $OUTPUT_FILE

OUTPUT_FILE=objects.py
echo -e 'object_list = [\n    "list is one-indexed",' > $OUTPUT_FILE
grep "^    [A-Z]" $NH_SOURCE/libnethack/src/objects.c | sed -e 's/[A-Z]*(//g' -e 's/,[A-Za-z ,0-9\)_\/\*=:"]*$/,/g' -e 's/DRGN_//g' -e 's/NULL/None/g' >> $OUTPUT_FILE
echo -e ']\ndef lookup_object(number):\n    object_ = object_list[number]\n    return object_' >> $OUTPUT_FILE
