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

lin atlas_N = mkN "Atlas" "Atlas" "Atlas" (variants {"Atlas" ; "Atlasses"}) "Atlas" "Atlas" masculine ;
lin bilge_N = mkN "Bilge" "Bilgen" ("Bilge" | "Bilgen") feminine ;
lin braunkohle_N = mkN braun_N (mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine) ;
lin braunkohlekraftwerk_N = mkN "Braunkohle" kraftwerk_N ;
lin chlorfluorkohlenwasserstoff_N = mkN "Chlorfluor" (mkN "Kohlen" wasserstoff_N) ;
-- Eier-, Torf-, and Zeichenkohle use -kohlen- recursively.
lin eierkohle_N = mkN "Eier" (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin fluorchlorkohlenwasserstoff_N = mkN "Fluorchlor" (mkN "Kohlen" wasserstoff_N) ;
lin gewebe_N = mkN "Gewebe" "Gewebe" ("Gewebe" | "Gewebs") neuter ;
lin halogenkohlenwasserstoff_N = mkN halogen_N (mkN "Kohlen" wasserstoff_N) ;
-- Prefer Holzkohlegrill; the now less common Holzkohlengrill is intentionally omitted.
lin holzkohle_N = mkN holz_N (mkN "Kohle" "Kohlen" "Kohle" feminine) ;
lin kanevas_N = mkN "Kanevas" "Kanevas" "Kanevas" (variants {"Kanevas" ; "Kanevasses"}) "Kanevas" "Kanevas" masculine ;
lin kohle_N = mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine ;
lin kohlebergwerk_N = mkN "Kohle" bergwerk_N ;
lin kohleheizung_N = mkN "Kohle" heizung_N ;
lin kohleherd_N = mkN "Kohle" herd_N ;
lin kohlehydrat_N = mkN "Kohle" hydrat_N ;
lin kohlehydratstruktur_N = mkN (mkN "Kohle" hydrat_N) struktur_N ;
lin kohlekraftwerk_N = mkN "Kohle" kraftwerk_N ;
lin kohlenbahn_N = mkN "Kohlen" bahn_N ;
lin kohlenfadenlampe_N = mkN (mkN "Kohlen" faden_N) lampe_N ;
lin kohlenherd_N = mkN "Kohlen" herd_N ;
lin kohlenhydrat_N = mkN "Kohlen" hydrat_N ;
lin kohlenhydratkette_N = mkN (mkN "Kohlen" hydrat_N) kette_N ;
lin kohlenhydratkomponente_N = mkN (mkN "Kohlen" hydrat_N) komponente_N ;
lin kohlenhydratmischung_N = mkN (mkN "Kohlen" hydrat_N) mischung_N ;
lin kohlenhydratstruktur_N = mkN (mkN "Kohlen" hydrat_N) struktur_N ;
lin kohlenmonoxidvergiftung_N = mkN (mkN "Kohlen" monoxid_N) vergiftung_N ;
lin kohlenmonoxydvergiftung_N = mkN "Kohlenmonoxyd" vergiftung_N ;
lin kohlensaeureanhydraseinhibitor_N = mkN (changeCompoundN "Kohlensäureanhydrase" (mkN (mkN "Kohlen" saeure_N) anhydrase_N)) inhibitor_N ;
lin kohlensaeurehaltig_A = regA "kohlensäurehaltig" ;
lin kohlenstoff_N = mkN "Kohlen" stoff_N ;
lin kohlenstoffatom_N = mkN (mkN "Kohlen" stoff_N) atom_N ;
lin kohlenstoffbindung_N = mkN (mkN "Kohlen" stoff_N) bindung_N ;
lin kohlenstoffeinheit_N = mkN (mkN "Kohlen" stoff_N) einheit_N ;
lin kohlenstoffhaltig_A = regA "kohlenstoffhaltig" ;
lin kohlenstoffkette_N = mkN (mkN "Kohlen" stoff_N) kette_N ;
lin kohlenstoffquelle_N = changeCompoundN "Kohlenstoffquellen" (mkN (mkN "Kohlen" stoff_N) quelle_N) ;
lin kohlenwasserstoff_N = mkN "Kohlen" wasserstoff_N ;
lin kohlenwasserstoffeinheit_N = mkN (mkN "Kohlen" wasserstoff_N) einheit_N ;
lin kohlenwasserstoffgruppe_N = mkN (mkN "Kohlen" wasserstoff_N) gruppe_N ;
lin kohlenwasserstoffkette_N = mkN (mkN "Kohlen" wasserstoff_N) kette_N ;
lin kohlenwasserstoffrest_N = mkN (mkN "Kohlen" wasserstoff_N) rest_N ;
lin kohletablette_N = mkN "Kohle" tablette_N ;
-- Historical Kohle- 'black', not Kohl 'cabbage'.
lin kohlmeise_N = mkN "Kohl" meise_N ;
lin kohlpechrabenschwarz_A = regA "kohlpechrabenschwarz" ;
lin kohlrabenschwarz_A = regA "kohlrabenschwarz" ; -- from "Kohle", i.e. referring to the blackness of coal
lin kohlroulade_N = mkN kohl_N roulade_N ;
lin kohlruebe_N = mkN kohl_N ruebe_N ;
lin kohlweissling_N = mkN kohl_N weissling_N ;
lin muehle_N = mkN "Mühle" "Mühlen" ("Mühl" | "Mühlen") feminine ;
lin mutterseelenallein_A = mkA (mkN mutter_N seele_N) allein_A ;
lin palme_N = mkN "Palme" "Palmen" ("Palm" | "Palmen") feminine ;
lin perfluorkohlenstoff_N = mkN "Perfluor" (mkN "Kohlen" stoff_N) ;
lin plan_b_N = mkN "Plan B" "Plan B" "Plan B" (variants {"Plan B" ; "Plans B"}) "Pläne B" "Plänen B" masculine ;
lin qualitaetswein_mit_praedikat_N = mkN "Qualitätswein mit Prädikat" "Qualitätswein mit Prädikat" "Qualitätswein mit Prädikat" (variants {"Qualitätsweins mit Prädikat" ; "Qualitätsweines mit Prädikat"}) "Qualitätsweine mit Prädikat" "Qualitätsweinen mit Prädikat" masculine ;
lin radiokohlenstoffdatierung_N = mkN (mkN "Radio" (mkN "Kohlen" stoff_N)) datierung_N ;
lin stammzelle_N = mkN stamm_N zelle_N ;
lin steinkohle_N = mkN stein_N (mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine) ;
lin steinkohlekraftwerk_N = mkN "Steinkohle" kraftwerk_N ;
lin torfkohle_N = mkN torf_N (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin verbrechen_gegen_die_menschlichkeit_CN = S.mkCN (mkN2 verbrechen_N (mkPrep "gegen" accusative)) (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;
lin vielverfaerbender_birkenpilz_CN = S.mkCN (mkA "Vielverfärbend") birkenpilz_N ;
lin zeichenkohle_N = mkN zeichen_N (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
}
