--# -path=.:../morphodict:alltenses

concrete DictGer of DictGerAbs =
  MorphoDictGer -
    [ atlas_N
    , bilge_N
    , creme_brulee_3_N
    , creme_brulee_N
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
lin alter_ego_N = changeCompoundN "Alter-Ego" (mkN "Alter Ego" "Alter Ego" "Alter Ego" (variants {"Alter Ego" ; "Alter Egos"}) "Alter Egos" "Alter Egos" neuter) ;
lin augenblicksbildung_N = mkN "Augenblicks" bildung_N ;
lin arbeitslosengeld_N = mkN "Arbeitslosen" geld_N ;
lin arbeitslosenquote_N = mkN "Arbeitslosen" quote_N ;
lin arbeitslosenrate_N = mkN "Arbeitslosen" rate_N ;
lin atlas_N = mkN "Atlas" "Atlas" "Atlas" (variants {"Atlas" ; "Atlasses"}) "Atlas" "Atlas" masculine ;
lin ausser_betrieb_Adv = mkAdv "außer Betrieb" ;
lin ausser_stande_Adv = mkAdv "außer Stande" ;
lin bad_bank_N = mkN "Bad Bank" "Bad Banks" "Bad-Bank" feminine ;
lin bauerngabel_N = mkN "Bauern" gabel_N ;
lin bilgenoel_N = mkN "Bilgen" oel_N ;
lin bilgenschwein_N = mkN "Bilgen" schwein_N ;
lin bilgeoel_N = mkN "Bilge" oel_N ;
lin bilgepumpe_N = mkN "Bilge" pumpe_N ;
lin besitzanzeigendes_fuerwort_CN = S.mkCN besitzanzeigend_A fuerwort_N ;
lin bildende_kunst_CN = S.mkCN bildend_A kunst_N ;
lin bilge_N = mkN "Bilge" "Bilgen" ("Bilge" | "Bilgen") feminine ;
lin braunkohle_N = mkN braun_N (mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine) ;
lin braunkohlekraftwerk_N = mkN "Braunkohle" kraftwerk_N ;
lin brevi_manu_Adv = mkAdv "brevi manu" ;
lin bundesverfassungsgericht_N = mkN bund_bundes_N verfassungsgericht_N ;
lin chlorfluorkohlenwasserstoff_N = mkN "Chlorfluor" (mkN "Kohlen" wasserstoff_N) ;
lin damengambit_N = mkN "Damen" gambit_N ;
lin damenfluegel_N = mkN "Damen" fluegel_N ;
lin drachenvariante_N = mkN "Drachen" variante_N ;
lin chef_de_partie_N = changeCompoundN "Chef-de-Partie"
  (mkN "Chef de Partie" "Chef de Partie" "Chef de Partie"
    "Chefs de Partie" "Chefs de Partie" "Chefs de Partie" masculine) ;
lin cordon_bleu_N = changeCompoundN "Cordon-bleu" (mkN "Cordon bleu" "Cordon bleu" "Cordon bleu" "Cordons bleus" "Cordons bleus" "Cordons bleus" neuter) ;
lin creme_brulee_3_N = mkN "Crème brûlée" "Crèmes brûlées" "Crème-brûlée" feminine ;
lin creme_brulee_N = mkN "Crème brulée" "Crèmes brulées" "Crème-brulée" feminine ;
lin dessen_ungeachtet_Adv = mkAdv "dessen ungeachtet" ;
lin epaulettenmatt_N = mkN "Epauletten" matt_N ;
lin diakritisches_zeichen_CN = S.mkCN diakritisch_A zeichen_N ;
lin direkte_rede_CN = S.mkCN direkt_A rede_N ;
lin echter_reizker_CN = S.mkCN (capitalizeA echt_A) reizker__N ;
-- Eier-, Torf-, and Zeichenkohle use -kohlen- recursively.
lin eierkohle_N = mkN "Eier" (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin enfant_terrible_N = changeCompoundN "Enfant-terrible" (mkN "Enfant terrible" "Enfant terrible" "Enfant terrible" "Enfants terribles" "Enfants terribles" "Enfants terribles" neuter) ;
lin en_passant_Adv = mkAdv "en passant" ;
lin en_vogue_Adv = mkAdv "en vogue" ;
lin fait_accompli_N = changeCompoundN "Fait-accompli" (mkN "Fait accompli" "Fait accompli" "Fait accompli" "Faits accomplis" "Faits accomplis" "Faits accomplis" neuter) ;
lin flektierende_sprache_CN = S.mkCN flektierend_A sprache_N ;
lin fluorchlorkohlenwasserstoff_N = mkN "Fluorchlor" (mkN "Kohlen" wasserstoff_N) ;
lin formale_sprache_CN = S.mkCN formal_A sprache_N ;
lin grundreihenmatt_N = mkN "Grundreihen" matt_N ;
lin fruehlingsknollenblaetterpilz_N = mkN "Frühlings" knollenblaetterpilz_N ;
lin fruehstueck_N = changeCompoundN "Frühstücks" (mkN "Früh" stueck_N) ;
lin fusionierende_sprache_CN = S.mkCN fusionierend_A sprache_N ;
lin genus_verbi_N = changeCompoundN "Genus-Verbi" (invarN "Genus Verbi" "Genera Verbi" neuter) ;
lin gewebeadhaesion_N = changeCompoundN "Gewebeadhäsions" (mkN "Gewebe" adhaesion_N) ;
lin gewebeoberflaeche_N = changeCompoundN "Gewebeoberflächen" (mkN "Gewebe" oberflaeche_N) ;
lin gewebefluessigkeit_N = changeCompoundN "Gewebeflüssigkeits" (mkN "Gewebe" fluessigkeit_N) ;
lin gewebeextrakt_N = mkN "Gewebe" extrakt_N ;
lin gewebefaktor_N = mkN "Gewebe" faktor_N ;
lin gewebefaktorproteinantagonist_N = changeCompoundN "Gewebefaktorproteinantagonisten" (mkN (mkN gewebefaktor_N protein_N) antagonist_N) ;
lin gewebeklebstoff_N = mkN "Gewebe" klebstoff_N ;
lin gewebekultur_N = mkN "Gewebe" kultur_N ;
lin gewebekulturmedium_N = mkN gewebekultur_N medium_N ;
lin gewebeschnitt_N = mkN "Gewebe" schnitt_N ;
lin gewebeschaedigung_N = changeCompoundN "Gewebeschädigungs" (mkN "Gewebe" schaedigung_N) ;
lin gewebestruktur_N = mkN "Gewebe" struktur_N ;
lin gewebsschaedigung_N = changeCompoundN "Gewebsschädigungs" (mkN "Gewebs" schaedigung_N) ;
lin gewebsschnitt_N = mkN "Gewebs" schnitt_N ;
lin gewebetransplantat_N = mkN "Gewebe" transplantat_N ;
lin gewebetransplantation_N = changeCompoundN "Gewebetransplantations" (mkN "Gewebe" transplantation_N) ;
lin gewebsverletzung_N = changeCompoundN "Gewebsverletzungs" (mkN "Gewebs" verletzung_N) ;
lin geburtstag_N = changeCompoundN "Geburtstags" (mkN "Geburts" tag_N) ;
lin geburtstagsfeier_N = mkN geburtstag_N feier_N ;
lin gewebe_N = mkN "Gewebe" "Gewebe" ("Gewebe" | "Gewebs") neuter ;
lin gruener_knollenblaetterpilz_CN = S.mkCN (capitalizeA gruen_A) knollenblaetterpilz_N ;
lin halogenkohlenwasserstoff_N = mkN halogen_N (mkN "Kohlen" wasserstoff_N) ;
lin handschuh_N = mkN "Hand" schuh_N ;
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
lin jour_fixe_N = changeCompoundN "Jour-fixe" (mkN "Jour fixe" "Jour fixe" "Jour fixe" "Jours fixes" "Jours fixes" "Jours fixes" masculine) ;
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
lin kinderspielzeug_N = mkN "Kinder" spielzeug_N ;
lin laeufergabel_N = mkN "Läufer" gabel_N ;
lin laeuferzug_N = mkN "Läufer" zug_N ;
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
lin lied_ohne_worte_N = changeCompoundN "Lied-ohne-Worte" (mkN "Lied ohne Worte" "Lied ohne Worte" "Lied ohne Worte" "Liedes ohne Worte" "Lieder ohne Worte" "Liedern ohne Worte" neuter) ;
lin millionen_mal_Adv = mkAdv "Millionen Mal" ;
lin maulwurffell_N = mkN "Maulwurf" fell_N ;
lin maulwurfsfell_N = mkN "Maulwurfs" fell_N ;
lin muehle_N = mkN "Mühle" "Mühlen" ("Mühl" | "Mühlen") feminine ;
lin muehlstein_N = mkN "Mühl" stein_N ;
lin mutterseelenallein_A = mkA (mkN mutter_N seele_N) allein_A ;
lin nach_links_Adv = mkAdv "nach links" ;
lin nach_rechts_Adv = mkAdv "nach rechts" ;
lin native_speaker_N = changeCompoundN "Native-Speaker" (mkN "Native Speaker" "Native Speaker" "Native Speaker" "Native Speaker" "Native Speakern" "Native Speaker" masculine) ;
lin natuerliche_sprache_CN = S.mkCN natuerlich_A sprache_N ;
lin noch_mal_Adv = mkAdv "noch mal" ;
lin otto_normalverbraucher_PN = mkPN "Otto Normalverbraucher" ;
lin orang_utan_eroeffnung_N = mkHyphenN "Orang-Utan" eroeffnung_N ;
lin palmengewoelbe_N = mkN "Palmen" gewoelbe_N ;
lin palmsonntag_N = changeCompoundN "Palmsonntags" (mkN "Palm" sonntag_N) ;
lin palmwein_N = mkN "Palm" wein_N ;
lin springergabel_N = mkN "Springer" gabel_N ;
lin springerzug_N = mkN "Springer" zug_N ;
lin palme_N = mkN "Palme" "Palmen" ("Palm" | "Palmen") feminine ;
lin par_excellence_Adv = mkAdv "par excellence" ;
lin par_force_Adv = mkAdv "par force" ;
lin per_annum_Adv = mkAdv "per annum" ;
lin per_os_Adv = mkAdv "per os" ;
lin perfluorkohlenstoff_N = mkN "Perfluor" (mkN "Kohlen" stoff_N) ;
lin peu_a_peu_Adv = mkAdv "peu à peu" ;
lin partielles_kurzwort_CN = S.mkCN partiell_A kurzwort_N ;
lin plan_b_N = mkN "Plan B" "Plan B" "Plan B" (variants {"Plan B" ; "Plans B"}) "Pläne B" "Plänen B" masculine ;
lin point_of_sale_N = changeCompoundN "Point-of-Sale" (mkN "Point of Sale" "Point of Sale" "Point of Sale" "Points of Sale" "Points of Sale" "Points of Sale" masculine) ;
lin post_mortem_Adv = mkAdv "post mortem" ;
lin pro_rata_Adv = mkAdv "pro rata" ;
lin public_viewing_N = changeCompoundN "Public-Viewing" (mkN "Public Viewing" "Public Viewing" "Public Viewing" (variants {"Public Viewing" ; "Public Viewings"}) "Public Viewings" "Public Viewings" neuter) ;
lin qualitaetswein_mit_praedikat_N = mkN "Qualitätswein mit Prädikat" "Qualitätswein mit Prädikat" "Qualitätswein mit Prädikat" (variants {"Qualitätsweins mit Prädikat" ; "Qualitätsweines mit Prädikat"}) "Qualitätsweine mit Prädikat" "Qualitätsweinen mit Prädikat" masculine ;
lin radiokohlenstoffdatierung_N = mkN (mkN "Radio" (mkN "Kohlen" stoff_N)) datierung_N ;
lin rotwein_N = mkN "Rot" wein_N ;
lin sans_phrase_Adv = mkAdv "sans phrase" ;
lin sauce_hollandaise_N = changeCompoundN "Sauce-Hollandaise"
  (invarN "Sauce hollandaise" feminine) ;
lin so_lala_Adv = mkAdv "so lala" ;
lin st_vincent_und_die_grenadinen_PN = mkPN
  "St. Vincent und die Grenadinen"
  "St. Vincent und die Grenadinen"
  "St. Vincent und den Grenadinen"
  "St. Vincents und der Grenadinen"
  neuter plural ;
lin stammzelle_N = mkN stamm_N zelle_N ;
lin stante_pede_Adv = mkAdv "stante pede" ;
lin stabat_mater_N = changeCompoundN "Stabat-Mater" (invarN "Stabat Mater" neuter) ;
lin steinkohle_N = mkN stein_N (mkN "Kohle" "Kohlen" ("Kohle" | "Kohlen") feminine) ;
lin steinkohlekraftwerk_N = mkN "Steinkohle" kraftwerk_N ;
lin torfkohle_N = mkN torf_N (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin toter_code_CN = S.mkCN tot_A code__N ;
lin up_to_date_Adv = mkAdv "up to date" ;
lin umweltfreundlich_A = mkA umwelt_N freundlich_A ;
lin vorstossvariante_N = mkN "Vorstoß" variante_N ;
lin verbrechen_gegen_die_menschlichkeit_CN = S.mkCN (mkN2 verbrechen_N (mkPrep "gegen" accusative)) (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;
lin verfassungsgericht_N = mkN verfassung_N gericht_N ;
lin vice_versa_Adv = mkAdv "vice versa" ;
lin viola_d_amore_N = changeCompoundN "Viola-d'Amore" (mkN "Viola d'Amore" "Viola d'Amore" "Viola d'Amore" "Viole d'Amore" "Viole d'Amore" "Violen d'Amore" feminine) ;
lin vielverfaerbender_birkenpilz_CN = S.mkCN (mkA "Vielverfärbend") birkenpilz_N ;
lin woertliche_rede_CN = S.mkCN woertlich_A rede_N ;
lin zeichenkohle_N = mkN zeichen_N (mkN "Kohle" "Kohlen" "Kohlen" feminine) ;
lin zipf_sche_gesetz_N = changeCompoundN "Zipf'sches-Gesetz"
  (mkN "Zipf'sches Gesetz" "Zipf'sches Gesetz" "Zipf'schem Gesetz"
    "Zipf'schen Gesetzes" "Zipf'sche Gesetze" "Zipf'schen Gesetzen" neuter) ;
lin zipfsche_gesetz_N = changeCompoundN "Zipfsches-Gesetz"
  (mkN "Zipfsches Gesetz" "Zipfsches Gesetz" "Zipfschem Gesetz"
    "Zipfschen Gesetzes" "Zipfsche Gesetze" "Zipfschen Gesetzen" neuter) ;
lin zu_hause_Adv = mkAdv "zu Hause" ;
lin zu_stande_Adv = mkAdv "zu Stande" ;
lin zu_tage_Adv = mkAdv "zu Tage" ;
lin zu_viel_Adv = mkAdv "zu viel" ;
}
