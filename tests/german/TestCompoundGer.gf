--# -path=.:../../dist/alltenses

concrete TestCompoundGer of TestCompoundGerAbs =
  ExtendGer ** open ParadigmsGer in {

flags coding=utf8 ; lexer=text ; unlexer=text ;

lin
  kaese_N = mkN "Käse" "Käse" "Käse" masculine ;
  frischkaese_N = mkN "Frisch" (mkN "Käse" "Käse" "Käse" masculine) ;
  kuchen_N = mkN "Kuchen" "Kuchen" "Kuchen" masculine ;
  frischkaesekuchen_N = mkN (mkN "Frisch" (mkN "Käse" "Käse" "Käse" masculine)) (mkN "Kuchen" "Kuchen" "Kuchen" masculine) ;
  sprache_N = mkN "Sprache" "Sprachen" "Sprach" feminine ;
  politik_N = mkN "Politik" "Politiken" "Politik" feminine ;
  sprachpolitik_N = mkN "Sprach" (mkN "Politik" "Politiken" "Politik" feminine) ;
  sprachenpolitik_N = mkN "Sprachen" (mkN "Politik" "Politiken" "Politik" feminine) ;
  hof_N = mkN "Hof" "Hof" "Hof" "Hofs" "Höfe" "Höfen" masculine ;
  friedhof_N = changeCompoundN "Friedhofs" (mkN "Fried" (mkN "Hof" "Hof" "Hof" "Hofs" "Höfe" "Höfen" masculine)) ;
  mauer_N = mkN "Mauer" "Mauern" "Mauer" feminine ;
  nah_A = regA "nah" ;
}
