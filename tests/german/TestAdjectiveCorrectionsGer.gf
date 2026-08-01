--# -path=.:../../dist/alltenses

resource TestAdjectiveCorrectionsGer = open DictGer, ResGer, Prelude in {

oper
  clean : Str =
    DictGer.braesig_A.s ! Posit ! APred
    ++ DictGer.braesig_A.s ! Compar ! APred
    ++ DictGer.braesig_A.s ! Superl ! APred
    ++ DictGer.deutsch_A.s ! Posit ! APred
    ++ DictGer.deutsch_A.s ! Compar ! APred
    ++ DictGer.deutsch_A.s ! Superl ! APred
    ++ DictGer.genuegsam_A.s ! Posit ! APred
    ++ DictGer.genuegsam_A.s ! Compar ! APred
    ++ DictGer.genuegsam_A.s ! Superl ! APred
    ++ DictGer.jaemmerlich_A.s ! Posit ! APred
    ++ DictGer.jaemmerlich_A.s ! Compar ! APred
    ++ DictGer.jaemmerlich_A.s ! Superl ! APred
    ++ DictGer.laecherlich_A.s ! Posit ! APred
    ++ DictGer.laecherlich_A.s ! Compar ! APred
    ++ DictGer.laecherlich_A.s ! Superl ! APred
    ++ DictGer.weitlaeufig_A.s ! Posit ! APred
    ++ DictGer.weitlaeufig_A.s ! Compar ! APred
    ++ DictGer.weitlaeufig_A.s ! Superl ! APred
    ++ DictGer.zuegellos_A.s ! Posit ! APred
    ++ DictGer.zuegellos_A.s ! Compar ! APred
    ++ DictGer.zuegellos_A.s ! Superl ! APred
    ++ DictGer.zutraeglich_A.s ! Posit ! APred
    ++ DictGer.zutraeglich_A.s ! Compar ! APred
    ++ DictGer.zutraeglich_A.s ! Superl ! APred
    ++ DictGer.frei_A.s ! Posit ! APred
    ++ DictGer.frei_A.s ! Compar ! APred
    ++ DictGer.frei_A.s ! Superl ! APred ;
}
