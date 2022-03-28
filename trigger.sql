create or replace function calculate_age()
returns trigger
as $$
declare
	calculated_age int;
begin
	calculated_age = date_part('year',age(new.dob));
	new.age = calculated_age;
	return new;
end;
$$ language plpgsql;


create trigger calc_age
before insert
on user_data
for each row
execute procedure calculate_age();