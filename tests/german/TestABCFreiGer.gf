--# -path=.:../../dist/alltenses

resource TestABCFreiGer = open DictGer, ParadigmsGer, ResGer, Prelude in {

oper
  forms : Str =
    DictGer.abc_waffen_N.s ! Pl ! Nom
    ++ DictGer.abc_waffen_N.co
    ++ DictGer.abc_waffen_frei_A.s ! Posit ! APred
    ++ DictGer.abc_waffen_frei_A.s ! Posit ! AMod (GSg Neutr) Nom
    ++ (ParadigmsGer.mkN DictGer.abc_waffen_N DictGer.system_N).s ! Sg ! Nom ;
}
