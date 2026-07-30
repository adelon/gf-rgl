--# -path=.:../../dist/alltenses

resource TestHochkompliziertGer = open DictGer, ResGer, Prelude in {

oper
  spaced = DictGer.hoch_kompliziert_AP ;

  spacedPred : Str = spaced.s ! APred ;
  spacedAttr : Str = spaced.s ! AMod (GSg Neutr) Nom ;
  spacedS2Nom : Str = spaced.s2 ! Nom ;
  spacedS2Acc : Str = spaced.s2 ! Acc ;
  spacedS2Dat : Str = spaced.s2 ! Dat ;
  spacedS2Gen : Str = spaced.s2 ! Gen ;
  spacedC1 : Str = spaced.c.p1 ;
  spacedC2 : Str = spaced.c.p2 ;
  spacedExt : Str = spaced.ext ;
  spacedIsPre : Str = case spaced.isPre of {
    True => "true" ;
    False => "false"
    } ;

  closedPos : Str = DictGer.hochkompliziert_A.s ! Posit ! APred ;
  closedCompar : Str = DictGer.hochkompliziert_A.s ! Compar ! APred ;
  closedSuperl : Str = DictGer.hochkompliziert_A.s ! Superl ! APred ;
}
