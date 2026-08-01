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

  canonical : Str =
    DictGer.barsch_A.s ! Posit ! APred ++ DictGer.barsch_A.s ! Compar ! APred ++ DictGer.barsch_A.s ! Superl ! APred
    ++ DictGer.doll_A.s ! Posit ! APred ++ DictGer.doll_A.s ! Compar ! APred ++ DictGer.doll_A.s ! Superl ! APred
    ++ DictGer.duester_A.s ! Posit ! APred ++ DictGer.duester_A.s ! Compar ! APred ++ DictGer.duester_A.s ! Superl ! APred
    ++ DictGer.flau_A.s ! Posit ! APred ++ DictGer.flau_A.s ! Compar ! APred ++ DictGer.flau_A.s ! Superl ! APred
    ++ DictGer.froh_A.s ! Posit ! APred ++ DictGer.froh_A.s ! Compar ! APred ++ DictGer.froh_A.s ! Superl ! APred
    ++ DictGer.gehoben_A.s ! Posit ! APred ++ DictGer.gehoben_A.s ! Compar ! APred ++ DictGer.gehoben_A.s ! Superl ! APred
    ++ DictGer.genau_A.s ! Posit ! APred ++ DictGer.genau_A.s ! Compar ! APred ++ DictGer.genau_A.s ! Superl ! APred
    ++ DictGer.hager_A.s ! Posit ! APred ++ DictGer.hager_A.s ! Compar ! APred ++ DictGer.hager_A.s ! Superl ! APred
    ++ DictGer.karg_A.s ! Posit ! APred ++ DictGer.karg_A.s ! Compar ! APred ++ DictGer.karg_A.s ! Superl ! APred
    ++ DictGer.lau_A.s ! Posit ! APred ++ DictGer.lau_A.s ! Compar ! APred ++ DictGer.lau_A.s ! Superl ! APred
    ++ DictGer.mau_A.s ! Posit ! APred ++ DictGer.mau_A.s ! Compar ! APred ++ DictGer.mau_A.s ! Superl ! APred
    ++ DictGer.morbid_A.s ! Posit ! APred ++ DictGer.morbid_A.s ! Compar ! APred ++ DictGer.morbid_A.s ! Superl ! APred
    ++ DictGer.morsch_A.s ! Posit ! APred ++ DictGer.morsch_A.s ! Compar ! APred ++ DictGer.morsch_A.s ! Superl ! APred
    ++ DictGer.neu_A.s ! Posit ! APred ++ DictGer.neu_A.s ! Compar ! APred ++ DictGer.neu_A.s ! Superl ! APred
    ++ DictGer.nieder_A.s ! Posit ! APred ++ DictGer.nieder_A.s ! Compar ! APred ++ DictGer.nieder_A.s ! Superl ! APred
    ++ DictGer.proper_A.s ! Posit ! APred ++ DictGer.proper_A.s ! Compar ! APred ++ DictGer.proper_A.s ! Superl ! APred
    ++ DictGer.rechtschaffen_A.s ! Posit ! APred ++ DictGer.rechtschaffen_A.s ! Compar ! APred ++ DictGer.rechtschaffen_A.s ! Superl ! APred
    ++ DictGer.rot_A.s ! Posit ! APred ++ DictGer.rot_A.s ! Compar ! APred ++ DictGer.rot_A.s ! Superl ! APred
    ++ DictGer.scheu_A.s ! Posit ! APred ++ DictGer.scheu_A.s ! Compar ! APred ++ DictGer.scheu_A.s ! Superl ! APred
    ++ DictGer.schmal_A.s ! Posit ! APred ++ DictGer.schmal_A.s ! Compar ! APred ++ DictGer.schmal_A.s ! Superl ! APred
    ++ DictGer.treu_A.s ! Posit ! APred ++ DictGer.treu_A.s ! Compar ! APred ++ DictGer.treu_A.s ! Superl ! APred
    ++ DictGer.tumb_A.s ! Posit ! APred ++ DictGer.tumb_A.s ! Compar ! APred ++ DictGer.tumb_A.s ! Superl ! APred
    ++ DictGer.verschieden_A.s ! Posit ! APred ++ DictGer.verschieden_A.s ! Compar ! APred ++ DictGer.verschieden_A.s ! Superl ! APred
    ++ DictGer.willkommen_A.s ! Posit ! APred ++ DictGer.willkommen_A.s ! Compar ! APred ++ DictGer.willkommen_A.s ! Superl ! APred
    ++ DictGer.zaeh_A.s ! Posit ! APred ++ DictGer.zaeh_A.s ! Compar ! APred ++ DictGer.zaeh_A.s ! Superl ! APred ;

  suffixal : Str =
    DictGer.buchstabengetreu_A.s ! Posit ! APred ++ DictGer.buchstabengetreu_A.s ! Compar ! APred ++ DictGer.buchstabengetreu_A.s ! Superl ! APred
    ++ DictGer.erdnah_A.s ! Posit ! APred ++ DictGer.erdnah_A.s ! Compar ! APred ++ DictGer.erdnah_A.s ! Superl ! APred
    ++ DictGer.fangfrisch_A.s ! Posit ! APred ++ DictGer.fangfrisch_A.s ! Compar ! APred ++ DictGer.fangfrisch_A.s ! Superl ! APred
    ++ DictGer.getreu_A.s ! Posit ! APred ++ DictGer.getreu_A.s ! Compar ! APred ++ DictGer.getreu_A.s ! Superl ! APred
    ++ DictGer.hartgesotten_A.s ! Posit ! APred ++ DictGer.hartgesotten_A.s ! Compar ! APred ++ DictGer.hartgesotten_A.s ! Superl ! APred
    ++ DictGer.ofenfrisch_A.s ! Posit ! APred ++ DictGer.ofenfrisch_A.s ! Compar ! APred ++ DictGer.ofenfrisch_A.s ! Superl ! APred
    ++ DictGer.postfrisch_A.s ! Posit ! APred ++ DictGer.postfrisch_A.s ! Compar ! APred ++ DictGer.postfrisch_A.s ! Superl ! APred
    ++ DictGer.sinnfrei_A.s ! Posit ! APred ++ DictGer.sinnfrei_A.s ! Compar ! APred ++ DictGer.sinnfrei_A.s ! Superl ! APred
    ++ DictGer.tiefschuerfend_A.s ! Posit ! APred ++ DictGer.tiefschuerfend_A.s ! Compar ! APred ++ DictGer.tiefschuerfend_A.s ! Superl ! APred
    ++ DictGer.voreingenommen_A.s ! Posit ! APred ++ DictGer.voreingenommen_A.s ! Compar ! APred ++ DictGer.voreingenommen_A.s ! Superl ! APred
    ++ DictGer.wortgetreu_A.s ! Posit ! APred ++ DictGer.wortgetreu_A.s ! Compar ! APred ++ DictGer.wortgetreu_A.s ! Superl ! APred ;

  compounds : Str =
    DictGer.saegerau_A.s ! Posit ! APred ++ DictGer.saegerau_A.s ! Compar ! APred ++ DictGer.saegerau_A.s ! Superl ! APred
    ++ DictGer.schadenfroh_A.s ! Posit ! APred ++ DictGer.schadenfroh_A.s ! Compar ! APred ++ DictGer.schadenfroh_A.s ! Superl ! APred
    ++ DictGer.wortkarg_A.s ! Posit ! APred ++ DictGer.wortkarg_A.s ! Compar ! APred ++ DictGer.wortkarg_A.s ! Superl ! APred ;
}
