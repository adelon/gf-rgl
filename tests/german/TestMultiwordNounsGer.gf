--# -path=.:../../dist/alltenses

resource TestMultiwordNounsGer = open DictGer, ParadigmsGer, SyntaxGer,
  ResGer, Prelude in {

oper
  sep : CompoundSep -> Str = \s -> case s of {
    HyphenSep => "hyphen" ;
    BindSep => "bind"
    } ;
  gender : Gender -> Str = \g -> case g of {
    Masc => "masculine" ;
    Fem => "feminine" ;
    Neutr => "neuter"
    } ;
  nounValue : Noun -> Str = \n -> n.s ! Sg ! Nom ++ n.s ! Sg ! Acc
    ++ n.s ! Sg ! Dat ++ n.s ! Sg ! Gen ++ n.s ! Pl ! Nom
    ++ n.s ! Pl ! Acc ++ n.s ! Pl ! Dat ++ n.s ! Pl ! Gen ++ n.co
    ++ n.uncap.s ! Sg ! Nom ++ n.uncap.s ! Sg ! Acc
    ++ n.uncap.s ! Sg ! Dat ++ n.uncap.s ! Sg ! Gen
    ++ n.uncap.s ! Pl ! Nom ++ n.uncap.s ! Pl ! Acc
    ++ n.uncap.s ! Pl ! Dat ++ n.uncap.s ! Pl ! Gen ++ n.uncap.co
    ++ sep n.csep ++ gender n.g ;

  badBank = DictGer.bad_bank_N ;
  badBankCompound = ParadigmsGer.mkN badBank DictGer.rettung_N ;
  badBankForms : Str = nounValue badBank ++ badBankCompound.s ! Sg ! Nom ;

  genusVerbi = DictGer.genus_verbi_N ;
  genusVerbiCompound = ParadigmsGer.mkN genusVerbi DictGer.system_N ;
  genusVerbiForms : Str = nounValue genusVerbi
    ++ genusVerbiCompound.s ! Sg ! Nom ;

  formalSg = SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
    DictGer.formale_sprache_CN ;
  formalPl = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
    DictGer.formale_sprache_CN ;
  diacriticSg = SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
    DictGer.diakritisches_zeichen_CN ;
  diacriticDat = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
    DictGer.diakritisches_zeichen_CN ;
  cnAgreement : Str = formalSg.s ! False ! Nom ++ formalPl.s ! False ! Dat
    ++ diacriticSg.s ! False ! Nom ++ diacriticDat.s ! False ! Dat ;

  fuerwortAndArtCitations : Str =
    DictGer.besitzanzeigendes_fuerwort_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.hinweisendes_fuerwort_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.bildende_kunst_CN.s ! Strong ! Sg ! Nom ;
  fuerwortAndArtAgreement : Str =
    (SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
      DictGer.besitzanzeigendes_fuerwort_CN).s ! False ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
      DictGer.hinweisendes_fuerwort_CN).s ! False ! Dat
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
      DictGer.bildende_kunst_CN).s ! False ! Nom ;

  speciesAndTerminologyCitations : Str =
    DictGer.echter_reizker_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.toter_code_CN.s ! Strong ! Sg ! Nom ;
  speciesAndTerminologyAgreement : Str =
    (SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
      DictGer.echter_reizker_CN).s ! False ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
      DictGer.echter_reizker_CN).s ! False ! Dat
    ++ (SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
      DictGer.toter_code_CN).s ! False ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
      DictGer.toter_code_CN).s ! False ! Dat ;

  englishLoanNounForms : Str =
    nounValue DictGer.hot_rod_N ++ nounValue DictGer.irish_stew_N
    ++ nounValue DictGer.public_viewing_N
    ++ (ParadigmsGer.mkN DictGer.hot_rod_N DictGer.system_N).s ! Sg ! Nom ;

  additionalLoanNounForms : Str = nounValue DictGer.alter_ego_N
    ++ nounValue DictGer.native_speaker_N ++ nounValue DictGer.point_of_sale_N ;

  englishConceptNounForms : Str = nounValue DictGer.big_bang_N
    ++ nounValue DictGer.big_brother_N
    ++ nounValue DictGer.corporate_identity_N ;

  fixedLoanNounForms : Str = nounValue DictGer.cordon_bleu_N
    ++ nounValue DictGer.enfant_terrible_N ++ nounValue DictGer.fait_accompli_N
    ++ nounValue DictGer.jour_fixe_N ;

  hyphenatedJNounForms : Str = nounValue DictGer.ja_nein_frage_N
    ++ nounValue DictGer.jam_session_N ++ nounValue DictGer.jo_jo_effekt_N
    ++ nounValue DictGer.jo_jo_N ;

  frenchCulinaryNounForms : Str = nounValue DictGer.creme_brulee_3_N
    ++ nounValue DictGer.creme_brulee_N ;

  partiellesKurzwortCitations : Str =
    DictGer.partielles_kurzwort_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.partielles_kurzwort_CN.s ! Strong ! Pl ! Nom ;
  partiellComparison : Str = partiell_A.s ! Compar ! APred
    ++ partiell_A.s ! Superl ! APred ;

  zipfLawForms : Str = nounValue DictGer.zipf_sche_gesetz_N
    ++ nounValue DictGer.zipfsche_gesetz_N ;

  sauceHollandaiseForms : Str = nounValue DictGer.sauce_hollandaise_N ;

  adjectiveCompoundForms : Str =
    DictGer.rotwein_N.s ! Sg ! Nom
    ++ DictGer.rotwein_N.s ! Pl ! Nom
    ++ DictGer.rotwein_N.co
    ++ (ParadigmsGer.mkN DictGer.rotwein_N DictGer.system_N).s ! Sg ! Nom
    ++ DictGer.umweltfreundlich_A.s ! Posit ! APred
    ++ DictGer.umweltfreundlich_A.s ! Posit ! AMod (GSg Neutr) Nom
    ++ DictGer.umweltfreundlich_A.s ! Compar ! APred
    ++ DictGer.umweltfreundlich_A.s ! Superl ! APred
    ++ DictGer.eiskalt_A.s ! Posit ! APred
    ++ DictGer.eiskalt_A.s ! Posit ! AMod (GSg Neutr) Nom
    ++ DictGer.eiskalt_A.s ! Compar ! APred
    ++ DictGer.eiskalt_A.s ! Superl ! APred
    ++ DictGer.abflusslos_A.s ! Posit ! APred
    ++ DictGer.abflusslos_A.s ! Posit ! AMod (GSg Neutr) Nom
    ++ DictGer.abflusslos_A.s ! Compar ! APred
    ++ DictGer.abflusslos_A.s ! Superl ! APred ;

  bilgeCompoundForms : Str =
    DictGer.bilgenoel_N.s ! Sg ! Nom
    ++ DictGer.bilgenoel_N.s ! Pl ! Nom
    ++ DictGer.bilgenoel_N.co
    ++ DictGer.bilgenschwein_N.s ! Sg ! Nom
    ++ DictGer.bilgenschwein_N.s ! Pl ! Nom
    ++ DictGer.bilgenschwein_N.co
    ++ DictGer.bilgeoel_N.s ! Sg ! Nom
    ++ DictGer.bilgeoel_N.s ! Pl ! Nom
    ++ DictGer.bilgeoel_N.co
    ++ DictGer.bilgepumpe_N.s ! Sg ! Nom
    ++ DictGer.bilgepumpe_N.s ! Pl ! Nom
    ++ DictGer.bilgepumpe_N.co
    ++ DictGer.bilgenentoeler_N.s ! Sg ! Nom
    ++ DictGer.bilgenentoeler_N.s ! Sg ! Gen
    ++ DictGer.bilgenentoeler_N.s ! Pl ! Nom
    ++ DictGer.bilgenentoeler_N.co ;

  chefDePartieForms : Str = nounValue DictGer.chef_de_partie_N ;

  chessCompoundForms : Str =
    DictGer.damengambit_N.s ! Sg ! Nom ++ DictGer.damengambit_N.s ! Pl ! Nom ++ DictGer.damengambit_N.co
    ++ DictGer.epaulettenmatt_N.s ! Sg ! Nom ++ DictGer.epaulettenmatt_N.s ! Pl ! Nom ++ DictGer.epaulettenmatt_N.co
    ++ DictGer.grundreihenmatt_N.s ! Sg ! Nom ++ DictGer.grundreihenmatt_N.s ! Pl ! Nom ++ DictGer.grundreihenmatt_N.co
    ++ DictGer.damenfluegel_N.s ! Sg ! Nom ++ DictGer.damenfluegel_N.s ! Pl ! Nom ++ DictGer.damenfluegel_N.co
    ++ DictGer.bauerngabel_N.s ! Sg ! Nom ++ DictGer.bauerngabel_N.s ! Pl ! Nom ++ DictGer.bauerngabel_N.co
    ++ DictGer.drachenvariante_N.s ! Sg ! Nom ++ DictGer.drachenvariante_N.s ! Pl ! Nom ++ DictGer.drachenvariante_N.co
    ++ DictGer.laeufergabel_N.s ! Sg ! Nom ++ DictGer.laeufergabel_N.s ! Pl ! Nom ++ DictGer.laeufergabel_N.co
    ++ DictGer.orang_utan_eroeffnung_N.s ! Sg ! Nom ++ DictGer.orang_utan_eroeffnung_N.s ! Pl ! Nom ++ DictGer.orang_utan_eroeffnung_N.co
    ++ DictGer.springergabel_N.s ! Sg ! Nom ++ DictGer.springergabel_N.s ! Pl ! Nom ++ DictGer.springergabel_N.co
    ++ DictGer.vorstossvariante_N.s ! Sg ! Nom ++ DictGer.vorstossvariante_N.s ! Pl ! Nom ++ DictGer.vorstossvariante_N.co
    ++ DictGer.familienschach_N.s ! Sg ! Nom ++ DictGer.familienschach_N.s ! Pl ! Nom ++ DictGer.familienschach_N.co
    ++ DictGer.vorgabepartie_N.s ! Sg ! Nom ++ DictGer.vorgabepartie_N.s ! Pl ! Nom ++ DictGer.vorgabepartie_N.co
    ++ DictGer.larsen_system_N.s ! Sg ! Nom ++ DictGer.larsen_system_N.s ! Pl ! Nom ++ DictGer.larsen_system_N.co ;

  lexicalizedModifierForms : Str =
    DictGer.muehlstein_N.s ! Sg ! Nom
    ++ DictGer.muehlstein_N.co
    ++ DictGer.palmengewoelbe_N.s ! Sg ! Nom
    ++ DictGer.palmengewoelbe_N.co
    ++ DictGer.palmsonntag_N.s ! Sg ! Nom
    ++ DictGer.palmsonntag_N.co
    ++ (ParadigmsGer.mkN DictGer.palmsonntag_N DictGer.prozession_N).s ! Sg ! Nom
    ++ DictGer.palmwein_N.s ! Sg ! Nom
    ++ DictGer.palmwein_N.co ;

  transparentCompoundForms : Str =
    DictGer.augenblicksbildung_N.s ! Sg ! Nom
    ++ DictGer.augenblicksbildung_N.s ! Sg ! Gen
    ++ DictGer.augenblicksbildung_N.s ! Pl ! Nom
    ++ DictGer.augenblicksbildung_N.co
    ++ (ParadigmsGer.mkN DictGer.augenblicksbildung_N DictGer.system_N).s ! Sg ! Nom
    ++ DictGer.fruehstueck_N.s ! Sg ! Nom
    ++ DictGer.fruehstueck_N.s ! Sg ! Gen
    ++ DictGer.fruehstueck_N.s ! Pl ! Nom
    ++ DictGer.fruehstueck_N.co
    ++ (ParadigmsGer.mkN DictGer.fruehstueck_N DictGer.system_N).s ! Sg ! Nom
    ++ DictGer.geburtstag_N.s ! Sg ! Nom
    ++ DictGer.geburtstag_N.s ! Sg ! Gen
    ++ DictGer.geburtstag_N.s ! Pl ! Nom
    ++ DictGer.geburtstag_N.co
    ++ DictGer.geburtstagsfeier_N.s ! Sg ! Nom
    ++ DictGer.geburtstagsfeier_N.co
    ++ (ParadigmsGer.mkN DictGer.geburtstag_N DictGer.system_N).s ! Sg ! Nom
    ++ DictGer.handschuh_N.s ! Sg ! Nom
    ++ DictGer.handschuh_N.s ! Sg ! Gen
    ++ DictGer.handschuh_N.s ! Pl ! Nom
    ++ DictGer.handschuh_N.co
    ++ (ParadigmsGer.mkN DictGer.handschuh_N DictGer.system_N).s ! Sg ! Nom ;

  musicalLoanNounForms : Str = nounValue DictGer.viola_d_amore_N ;

  musicalPhraseNounForms : Str = nounValue DictGer.lied_ohne_worte_N ;

  invariantLatinNounForms : Str = nounValue DictGer.stabat_mater_N ;

  languageTypeCitations : Str =
    DictGer.agglutinierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.analytische_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.ausgestorbene_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.baltische_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.flektierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.fusionierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.germanische_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.iranische_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.isolierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.keltische_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.lebende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.natuerliche_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.romanische_sprache_CN.s ! Strong ! Sg ! Nom ;
  fusionSg = SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
    DictGer.fusionierende_sprache_CN ;
  fusionDat = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
    DictGer.fusionierende_sprache_CN ;
  isolationPl = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
    DictGer.isolierende_sprache_CN ;
  languageTypeAgreement : Str = fusionSg.s ! False ! Nom
    ++ fusionDat.s ! False ! Dat ++ isolationPl.s ! False ! Dat
    ++ (SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
      DictGer.analytische_sprache_CN).s ! False ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
      DictGer.germanische_sprache_CN).s ! False ! Dat
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
      DictGer.romanische_sprache_CN).s ! False ! Dat ;

  reportedSpeechCitations : Str =
    DictGer.direkte_rede_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.indirekte_rede_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.woertliche_rede_CN.s ! Strong ! Sg ! Nom ;
  directDat = SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
    DictGer.direkte_rede_CN ;
  indirectPl = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
    DictGer.indirekte_rede_CN ;
  literalDat = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
    DictGer.woertliche_rede_CN ;
  reportedSpeechAgreement : Str = directDat.s ! False ! Dat
    ++ indirectPl.s ! False ! Nom ++ literalDat.s ! False ! Dat ;

  greenFungus = DictGer.gruener_knollenblaetterpilz_CN ;
  greenFungusDat = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
    greenFungus ;
  greenFungusPl = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
    greenFungus ;
  speciesForms : Str = greenFungus.s ! Strong ! Sg ! Nom
    ++ greenFungusDat.s ! False ! Dat ++ greenFungusPl.s ! False ! Nom ;

  additionalSpeciesCitations : Str =
    DictGer.gelbe_kantherelle_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.gelbe_kraterelle_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.loeffelfoermige_seitling_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.roetende_schirmling_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.starkriechende_pfifferling_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.ziegelrote_risspilz_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.weiterfuehrende_nebensatz_CN.s ! Strong ! Sg ! Nom ;
  additionalSpeciesAgreement : Str =
    (SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
      DictGer.loeffelfoermige_seitling_CN).s ! False ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
      DictGer.roetende_schirmling_CN).s ! False ! Dat
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
      DictGer.weiterfuehrende_nebensatz_CN).s ! False ! Dat ;

  variierendeTerminologyCitations : Str =
    DictGer.frei_variierendes_allomorph_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.frei_variierendes_allophon_CN.s ! Strong ! Pl ! Nom ;
  variierendeTerminologyAgreement : Str =
    (SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
      DictGer.frei_variierendes_allomorph_CN).s ! False ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
      DictGer.frei_variierendes_allophon_CN).s ! False ! Dat ;

  ewigesSchachForms : Str = nounValue DictGer.ewige_schach_N ;

  leipzigerAllerleiForms : Str =
    DictGer.leipziger_allerlei_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.leipziger_allerlei_CN.s ! Strong ! Sg ! Gen
    ++ DictGer.leipziger_allerlei_CN.s ! Strong ! Pl ! Nom
    ++ (SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
      DictGer.leipziger_allerlei_CN).s ! False ! Dat ;

  correctedPhraseForms : Str = nounValue
    DictGer.qualitaetswein_bestimmter_anbaugebiete_N
    ++ nounValue DictGer.zahl_null_N ;

  latinPhraseForms : Str = nounValue DictGer.capsulitis_adhaesiva_N ;

  childOfGod = DictGer.kind_gottes_CN ;
  childOfGodSg = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
    childOfGod ;
  childOfGodPl = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
    childOfGod ;
  childOfGodForms : Str = childOfGodSg.s ! False ! Nom
    ++ childOfGodSg.s ! False ! Gen ++ childOfGodPl.s ! False ! Nom ;

  otto = DictGer.otto_normalverbraucher_PN ;
  stVincent = DictGer.st_vincent_und_die_grenadinen_PN ;
  properNameForms : Str = otto.s ! Nom ++ otto.s ! Gen
    ++ case otto.n of {Sg => "singular" ; _ => "wrong"}
    ++ stVincent.s ! Nom ++ stVincent.s ! Acc ++ stVincent.s ! Dat
    ++ stVincent.s ! Gen
    ++ case stVincent.n of {Pl => "plural" ; _ => "wrong"} ;

  fungus = DictGer.knollenblaetterpilz_N ;
  springFungus = DictGer.fruehlingsknollenblaetterpilz_N ;
  springCompound = ParadigmsGer.mkN DictGer.fruehling_N DictGer.anfang_N ;
  fungusFamily : Str = fungus.s ! Sg ! Nom ++ fungus.s ! Sg ! Gen
    ++ fungus.s ! Pl ! Nom ++ fungus.co ++ springFungus.s ! Sg ! Nom
    ++ springFungus.s ! Pl ! Nom ++ springFungus.co ++ DictGer.fruehling_N.co
    ++ springCompound.s ! Sg ! Nom ;
}
