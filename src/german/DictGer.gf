--# -path=.:../morphodict:alltenses

concrete DictGer of DictGerAbs =
  MorphoDictGer -
    [ bilge_N
    , braunkohle_N
    , gewebe_N
    , kohle_N
    , muehle_N
    , palme_N
    , stammzelle_N
    , steinkohle_N
    ] **
  open ParadigmsGer, (S = SyntaxGer) in {

flags coding=utf8 ;

lin
  bilge_N = mkN "Bilge" "Bilgen" ("Bilge" | "Bilgen") feminine ;

  braunkohle_N =
    mkN "Braunkohle" "Braunkohlen" ("Braunkohle" | "Braunkohlen") feminine ;

  gewebe_N = mkN "Gewebe" "Gewebe" ("Gewebe" | "Gewebs") neuter ;

  kohle_N = mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine ;

  muehle_N = mkN "Mühle" "Mühlen" ("Mühl" | "Mühlen") feminine ;

  palme_N = mkN "Palme" "Palmen" ("Palm" | "Palmen") feminine ;

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

  stammzelle_N =
    mkN "Stammzelle" "Stammzellen" ("Stammzell" | "Stammzellen") feminine ;

  steinkohle_N =
    mkN "Steinkohle" "Steinkohlen" ("Steinkohle" | "Steinkohlen") feminine ;

  verbrechen_gegen_die_menschlichkeit_CN =
    S.mkCN
      (mkN2 verbrechen_N (mkPrep "gegen" accusative))
      (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;

  vielverfaerbender_birkenpilz_CN =
    S.mkCN (mkA "Vielverfärbend") birkenpilz_N ;
}
