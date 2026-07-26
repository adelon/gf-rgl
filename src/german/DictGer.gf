--# -path=.:../morphodict:alltenses

concrete DictGer of DictGerAbs =
  MorphoDictGer **
  open ParadigmsGer, (S = SyntaxGer) in {

flags coding=utf8 ;

lin
  plan_b_N =
    mkN "Plan B" "Plan B" "Plan B" (variants {"Plan B" ; "Plans B"})
        "Pläne B" "Plänen B" masculine ;

  qualitaetswein_mit_praedikat_N =
    mkN "Qualitätswein mit Prädikat"
        "Qualitätswein mit Prädikat"
        "Qualitätswein mit Prädikat"
        (variants {"Qualitätsweins mit Prädikat" ; "Qualitätsweines mit Prädikat"})
        "Qualitätsweine mit Prädikat"
        "Qualitätsweinen mit Prädikat"
        masculine ;

  verbrechen_gegen_die_menschlichkeit_CN =
    S.mkCN
      (mkN2 verbrechen_N (mkPrep "gegen" accusative))
      (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;

  vielverfaerbender_birkenpilz_CN =
    S.mkCN (mkA "Vielverfärbend") birkenpilz_N ;
}
