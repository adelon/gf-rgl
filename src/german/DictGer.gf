--# -path=.:../morphodict:alltenses

concrete DictGer of DictGerAbs =
  MorphoDictGer **
  open ParadigmsGer, (S = SyntaxGer) in {

flags coding=utf8 ;

lin
  verbrechen_gegen_die_menschlichkeit_CN =
    S.mkCN
      (mkN2 verbrechen_N (mkPrep "gegen" accusative))
      (S.mkNP S.the_Quant S.singularNum menschlichkeit_N) ;
}
