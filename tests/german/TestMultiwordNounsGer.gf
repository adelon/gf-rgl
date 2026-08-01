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
