#!/bin/bash
trap "pgrep python | xargs kill && kill -- -$$" SIGINT


run () {
    local i=$1
    echo "Starting process for $i"
    # replace with the slide num
    if [[ -f "sparsemat_slide_hole_trans_$i.txt" ]]; then
        echo "skipping $i time expand bc done"
    else 
        sed -i '' -e "s/slide_num = [0-9]*/slide_num = $i/" TimeExpandedRipsComplexSlideRobustnessCheck.py
        python TimeExpandedRipsComplexSlideRobustnessCheck.py
    fi
    echo "$i moving to processing"
    if [[ -f "output_slide_hole_$i.txt" ]]; then
        echo "skipping $i process ripser bc done"
    else 
        sed -i '' -e "s/slide_num = [0-9]*/slide_num = $i/" ProcessRipserC++SlideRobustnessCheck.py
        python ProcessRipserC++SlideRobustnessCheck.py
    fi

}

for file in "RobustIsochrones"/*
do
    sleep 1
    arr=(${file//_/ })
    end=${arr[4]}
    other=(${end//-/ })
    i=${other[0]}
    ((j=j%5)); ((j++==0)) && wait
    run "$i" &
    # pids+=($!)
    # echo "${pids[@]}"
    
done
