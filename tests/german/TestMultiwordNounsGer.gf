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

  languageTypeCitations : Str =
    DictGer.agglutinierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.flektierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.fusionierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.isolierende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.lebende_sprache_CN.s ! Strong ! Sg ! Nom
    ++ DictGer.natuerliche_sprache_CN.s ! Strong ! Sg ! Nom ;
  fusionSg = SyntaxGer.mkNP SyntaxGer.a_Quant SyntaxGer.singularNum
    DictGer.fusionierende_sprache_CN ;
  fusionDat = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.singularNum
    DictGer.fusionierende_sprache_CN ;
  isolationPl = SyntaxGer.mkNP SyntaxGer.the_Quant SyntaxGer.pluralNum
    DictGer.isolierende_sprache_CN ;
  languageTypeAgreement : Str = fusionSg.s ! False ! Nom
    ++ fusionDat.s ! False ! Dat ++ isolationPl.s ! False ! Dat ;

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
