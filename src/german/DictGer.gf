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

lin a_achse_N = mkHyphenN a_N achse_N ;
lin a_battuta_Adv = mkAdv "a battuta" ;
lin a_cappella_Adv = mkAdv "a cappella" ;
lin a_jour_Adv = mkAdv "à jour" ;
lin a_posteriori_Adv = mkAdv "a posteriori" ;
lin a_priori_Adv = mkAdv "a priori" ;
lin ad_acta_Adv = mkAdv "ad acta" ;
lin ad_nauseam_Adv = mkAdv "ad nauseam" ;
lin agglutinierende_sprache_CN = S.mkCN agglutinierend_A sprache_N ;
lin arbeitslosengeld_N = mkN "Arbeitslosen" geld_N ;
lin arbeitslosenquote_N = mkN "Arbeitslosen" quote_N ;
lin arbeitslosenrate_N = mkN "Arbeitslosen" rate_N ;
lin atlas_N = mkN "Atlas" "Atlas" "Atlas" (variants {"Atlas" ; "Atlasses"}) "Atlas" "Atlas" masculine ;
lin ausser_betrieb_Adv = mkAdv "außer Betrieb" ;
lin ausser_stande_Adv = mkAdv "außer Stande" ;
lin bad_bank_N = mkN "Bad Bank" "Bad Banks" "Bad-Bank" feminine ;
lin besitzanzeigendes_fuerwort_CN = S.mkCN besitzanzeigend_A fuerwort_N ;
lin bildende_kunst_CN = S.mkCN bildend_A kunst_N ;
lin bilge_N = mkN "Bilge" "Bilgen" ("Bilge" | "Bilgen") feminine ;
lin braunkohle_N = mkN braun_N (mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine) ;
lin braunkohlekraftwerk_N = mkN "Braunkohle" kraftwerk_N ;
lin brevi_manu_Adv = mkAdv "brevi manu" ;
lin bundesverfassungsgericht_N = mkN bund_bundes_N verfassungsgericht_N ;
lin chlorfluorkohlenwasserstoff_N = mkN "Chlorfluor" (mkN "Kohlen" wasserstoff_N) ;
lin dessen_ungeachtet_Adv = mkAdv "dessen ungeachtet" ;
lin diakritisches_zeichen_CN = S.mkCN diakritisch_A zeichen_N ;
lin direkte_rede_CN = S.mkCN direkt_A rede_N ;
lin echter_reizker_CN = S.mkCN (capitalizeA echt_A) reizker__N ;
-- Eier-, Torf-, and Zeichenkohle use -kohlen- recursively.
lin eierkohle_N = mkN "Eier" (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin en_passant_Adv = mkAdv "en passant" ;
lin en_vogue_Adv = mkAdv "en vogue" ;
lin flektierende_sprache_CN = S.mkCN flektierend_A sprache_N ;
lin fluorchlorkohlenwasserstoff_N = mkN "Fluorchlor" (mkN "Kohlen" wasserstoff_N) ;
lin formale_sprache_CN = S.mkCN formal_A sprache_N ;
lin fruehlingsknollenblaetterpilz_N = mkN "Frühlings" knollenblaetterpilz_N ;
lin fusionierende_sprache_CN = S.mkCN fusionierend_A sprache_N ;
lin genus_verbi_N = changeCompoundN "Genus-Verbi" (invarN "Genus Verbi" "Genera Verbi" neuter) ;
lin gewebe_N = mkN "Gewebe" "Gewebe" ("Gewebe" | "Gewebs") neuter ;
lin gruener_knollenblaetterpilz_CN = S.mkCN (capitalizeA gruen_A) knollenblaetterpilz_N ;
lin halogenkohlenwasserstoff_N = mkN halogen_N (mkN "Kohlen" wasserstoff_N) ;
lin hinweisendes_fuerwort_CN = S.mkCN hinweisend_A fuerwort_N ;
lin hoch_kompliziert_AP = S.mkAP (mkAdA "hoch") kompliziert_A ;
-- Prefer Holzkohlegrill; the now less common Holzkohlengrill is intentionally omitted.
lin holzkohle_N = mkN holz_N (mkN "Kohle" "Kohlen" "Kohle" feminine) ;
lin hot_rod_N = changeCompoundN "Hot-Rod" (mkN "Hot Rod" "Hot Rod" "Hot Rod" "Hot Rods" "Hot Rods" "Hot Rods" neuter) ;
lin in_ermangelung_Adv = mkAdv "in Ermangelung" ;
lin in_ermanglung_Adv = mkAdv "in Ermanglung" ;
lin in_petto_Adv = mkAdv "in petto" ;
lin indirekte_rede_CN = S.mkCN indirekt_A rede_N ;
lin irish_stew_N = changeCompoundN "Irish-Stew" (mkN "Irish Stew" "Irish Stew" "Irish Stew" (variants {"Irish Stew" ; "Irish Stews"}) "Irish Stews" "Irish Stews" neuter) ;
lin isolierende_sprache_CN = S.mkCN isolierend_A sprache_N ;
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
lin kind_gottes_CN = S.mkCN (mkN2 kind_N genPrep) (S.mkNP (mkPN "Gott" "Gottes" masculine)) ;
lin knollenblaetterpilz_N = mkN "Knollenblätter" pilz_N ;
-- Historical Kohle- 'black', not Kohl 'cabbage'.
lin kohlmeise_N = mkN "Kohl" meise_N ;
lin kohlpechrabenschwarz_A = regA "kohlpechrabenschwarz" ;
lin kohlrabenschwarz_A = regA "kohlrabenschwarz" ; -- from "Kohle", i.e. referring to the blackness of coal
lin kohlroulade_N = mkN kohl_N roulade_N ;
lin kohlruebe_N = mkN kohl_N ruebe_N ;
lin kohlweissling_N = mkN kohl_N weissling_N ;
lin last_minute_Adv = mkAdv "last minute" ;
lin lebende_sprache_CN = S.mkCN lebend_A sprache_N ;
lin liebesbrief_N = mkN liebe_N brief_N ;
lin millionen_mal_Adv = mkAdv "Millionen Mal" ;
lin muehle_N = mkN "Mühle" "Mühlen" ("Mühl" | "Mühlen") feminine ;
lin mutterseelenallein_A = mkA (mkN mutter_N seele_N) allein_A ;
lin nach_links_Adv = mkAdv "nach links" ;
lin nach_rechts_Adv = mkAdv "nach rechts" ;
lin natuerliche_sprache_CN = S.mkCN natuerlich_A sprache_N ;
lin noch_mal_Adv = mkAdv "noch mal" ;
lin otto_normalverbraucher_PN = mkPN "Otto Normalverbraucher" ;
lin palme_N = mkN "Palme" "Palmen" ("Palm" | "Palmen") feminine ;
lin par_excellence_Adv = mkAdv "par excellence" ;
lin par_force_Adv = mkAdv "par force" ;
lin per_annum_Adv = mkAdv "per annum" ;
lin per_os_Adv = mkAdv "per os" ;
lin perfluorkohlenstoff_N = mkN "Perfluor" (mkN "Kohlen" stoff_N) ;
lin peu_a_peu_Adv = mkAdv "peu à peu" ;
lin plan_b_N = mkN "Plan B" "Plan B" "Plan B" (variants {"Plan B" ; "Plans B"}) "Pläne B" "Plänen B" masculine ;
lin post_mortem_Adv = mkAdv "post mortem" ;
lin pro_rata_Adv = mkAdv "pro rata" ;
lin public_viewing_N = changeCompoundN "Public-Viewing" (mkN "Public Viewing" "Public Viewing" "Public Viewing" (variants {"Public Viewing" ; "Public Viewings"}) "Public Viewings" "Public Viewings" neuter) ;
lin qualitaetswein_mit_praedikat_N = mkN "Qualitätswein mit Prädikat" "Qualitätswein mit Prädikat" "Qualitätswein mit Prädikat" (variants {"Qualitätsweins mit Prädikat" ; "Qualitätsweines mit Prädikat"}) "Qualitätsweine mit Prädikat" "Qualitätsweinen mit Prädikat" masculine ;
lin radiokohlenstoffdatierung_N = mkN (mkN "Radio" (mkN "Kohlen" stoff_N)) datierung_N ;
lin sans_phrase_Adv = mkAdv "sans phrase" ;
lin so_lala_Adv = mkAdv "so lala" ;
lin st_vincent_und_die_grenadinen_PN = mkPN
  "St. Vincent und die Grenadinen"
  "St. Vincent und die Grenadinen"
  "St. Vincent und den Grenadinen"
  "St. Vincents und der Grenadinen"
  neuter plural ;
lin stammzelle_N = mkN stamm_N zelle_N ;
lin stante_pede_Adv = mkAdv "stante pede" ;
lin steinkohle_N = mkN stein_N (mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine) ;
lin steinkohlekraftwerk_N = mkN "Steinkohle" kraftwerk_N ;
lin torfkohle_N = mkN torf_N (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin toter_code_CN = S.mkCN tot_A code__N ;
lin up_to_date_Adv = mkAdv "up to date" ;
lin verbrechen_gegen_die_menschlichkeit_CN = S.mkCN (mkN2 verbrechen_N (mkPrep "gegen" accusative)) (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;
lin verfassungsgericht_N = mkN verfassung_N gericht_N ;
lin vice_versa_Adv = mkAdv "vice versa" ;
lin vielverfaerbender_birkenpilz_CN = S.mkCN (mkA "Vielverfärbend") birkenpilz_N ;
lin woertliche_rede_CN = S.mkCN woertlich_A rede_N ;
lin zeichenkohle_N = mkN zeichen_N (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin zu_hause_Adv = mkAdv "zu Hause" ;
lin zu_stande_Adv = mkAdv "zu Stande" ;
lin zu_tage_Adv = mkAdv "zu Tage" ;
lin zu_viel_Adv = mkAdv "zu viel" ;
}
