delete from ir_model_constraint where model in (select id from ir_model where model in ('smo.quotaintion.indication','smo.quotaintion.treatment','smo.quotaintion.clinical.stage'));
delete from ir_model_fields where model_id in (select id from ir_model where model in ('smo.quotaintion.indication','smo.quotaintion.treatment','smo.quotaintion.clinical.stage'));
delete from ir_model_relation where model in (select id from ir_model where model in ('smo.quotaintion.indication','smo.quotaintion.treatment','smo.quotaintion.clinical.stage'));
delete from ir_model where model in ('smo.quotaintion.indication','smo.quotaintion.treatment','smo.quotaintion.clinical.stage');
delete from ir_model_data where model in ('smo.quotaintion.indication','smo.quotaintion.treatment','smo.quotaintion.clinical.stage');

