MAIN

1x2

home
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[1]

/html/body/div[1]/div/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[1]
draw
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[2]
away
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[3]



over/under

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[2]/div[1]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[2]/div[2]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[2]/div[3]


/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[3]/div[1]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[3]/div[2]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[3]/div[3]


/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[4]/div[1]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[4]/div[2]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[3]/div[2]/div/div[4]/div[3]



asian handicap

home
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[2]/div[1]

away
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[2]/div[2]

home
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[3]/div[1]

away
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[3]/div[2]




HALFTIME

halftime button menu opath
/html/body/div[1]/div/div[1]/main/div/div[2]/div/div/div[3]/div/div[1]/div/ul/li[5]

home
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[1]

draw
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[2]

away
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[1]/div[2]/div/div/div[3]


over/under

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div[2]/div[1]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div[2]/div[2]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div[2]/div[3]


/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div[3]/div[1]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div[3]/div[2]

/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[2]/div[2]/div/div[3]/div[3]


asian handicap

home
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[2]/div[1]

away
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[2]/div[2]


home
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[3]/div[1]

away
/html/body/div[1]/div/div[2]/main/div/div[2]/div/div/div[3]/div/div[2]/div[15]/div[2]/div/div[3]/div[2]


so for the selectors i want to chnage what is being used:

so use class "m-market-row m-market-row--3" get all dovs with that class 
now for 1x2 , first div form the lsit is for 1x2 now get classs "has-desc m-outcome multiple" to get all the divs for hom draw and away respecitvely the first one is home seocnd draw 3rd away. use the nner classes of each to get the clss "odds" for the odds value to confirm the right odds

- for over/under get all divs with classs "m-market-specifier" , the first one is for over/under then get list of diovs with class "m-market-row m-market-row"  each of them contains each over/under 1.5 2.5 all list that are avaible basiclal for that game for over/under. now loop over to get the correct one that is being looked for for example is over 1.5 check the div that has the inneve div of clas "m-outcome m-outcome-desc" span text of 1.5 then to get the odds using the div of class "m-outcome" inner to the "m-market-row m-market-row" there are usualy 2 list the first is for over the second for under. then get the inner div  of class "dds" of the div "m-outcome" to get the actual odds and confirm.

- now for asian handicap, get div of class "m-market-handicap" might be the only one or just tske the first then get all the inner divs of clsss "m-market-row m-market-row" to odds (home, away for the game) for example if looking for away +0.5 then loop through and go to the inner r each to get div of class "has-desc m-outcome multiple" the first div if home seocnd one is away, then inner again get div of clsass "desc"to knwo for the +0.5 and div of class "odds" to get actual odds to confirm