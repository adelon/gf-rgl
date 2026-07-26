--# -path=.:../morphodict:alltenses

concrete DictGer of DictGerAbs =
  MorphoDictGer -
    [ atlas_N
    , bilge_N
    , gewebe_N
    , kanevas_N
    , kohle_N
    , muehle_N
    , palme_N
    ] **
  open ParadigmsGer, (S = SyntaxGer) in {

flags coding=utf8 ;

oper
  kohleVariant_N : N =
    mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine ;

lin
  atlas_N =
    mkN "Atlas" "Atlas" "Atlas" (variants {"Atlas" ; "Atlasses"})
        "Atlas" "Atlas" masculine ;

  bilge_N = mkN "Bilge" "Bilgen" ("Bilge" | "Bilgen") feminine ;

  braunkohle_N = mkN braun_N kohleVariant_N ;

  gewebe_N = mkN "Gewebe" "Gewebe" ("Gewebe" | "Gewebs") neuter ;

  kanevas_N =
    mkN "Kanevas" "Kanevas" "Kanevas"
        (variants {"Kanevas" ; "Kanevasses"}) "Kanevas" "Kanevas" masculine ;

  kohle_N = kohleVariant_N ;

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

  stammzelle_N = mkN stamm_N zelle_N ;

  steinkohle_N = mkN stein_N kohleVariant_N ;

  verbrechen_gegen_die_menschlichkeit_CN =
    S.mkCN
      (mkN2 verbrechen_N (mkPrep "gegen" accusative))
      (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;

  vielverfaerbender_birkenpilz_CN =
    S.mkCN (mkA "Vielverfärbend") birkenpilz_N ;
}
