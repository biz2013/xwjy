delete from users_orderchangelog;
delete from users_userreview;
delete from users_order;
delete from users_userwallet;
delete from users_userstatue;
delete from users_wallet;
delete from users_cryptocurrency;
delete from users_userpaymentmethod;
delete from users_paymentprovider;
delete from users_user;

/* trick to skip foreign key check
  django does not explicitly make on_delete=cascade on 
  foreign_key
*/
set foreign_key_checks=0;
delete from users_userlogin;
set foreign_key_checks=1;

insert into users_userlogin(username, passwd_hash, alias, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('sysop','5d381d1c4e755e6784e036736a78e871613d7b58c2d1b8d66cc4fe3b162e8807', '', '', 'sysop', now(), 'sysop', now());                    
insert into users_userlogin(username, passwd_hash, alias, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('yingzhou','58d8432c2385d6873fc3f84295286b7be3c84dc0e3fbfe4900fdd62fd1794ba5', '', '', 'sysop', now(), 'sysop', now());
insert into users_userlogin(username, passwd_hash, alias, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('taozhang','8e1e3e91a4c2c09402a0fa18090e0d3970ff40cf25cae28e9879baf83675c391', '', '', 'sysop', now(), 'sysop', now());
insert into users_userlogin(username, passwd_hash, alias, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('chiwang','df18526b20e73eae33e09f6014e9dff5d03ef045d5eb89841247471b216c9abd', '', '', 'sysop', now(), 'sysop', now());

insert into users_user(login_id, firstname, middle, lastname, email, phone, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at)
 select u.username, 'root', '', '', 'tttzhang2000@yahoo.com', '', '', 'sysop', now(), 'sysop', now() from users_userlogin u where u.username='taozhang' ;
insert into users_user(login_id, firstname, middle, lastname, email, phone, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values ('yingzhou', 'ying', '', 'zhou', 'yingzhou61@yahoo.com', '', '', 'sysop', now(), 'sysop', now());
insert into users_user(login_id, firstname, middle, lastname, email, phone, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values ('chiwang', 'chi', '', 'wang', 'alex.chi.wang@gmail.com', '', '', 'sysop', now(), 'sysop', now());

insert into users_paymentprovider(name, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('weixin', '', 'sysop', now(),'sysop', now());

insert into users_cryptocurrency (currency_code, name, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('AXFund','AXFund', 'sysop', now(), 'sysop',now());

insert into users_userpaymentmethod (account_at_provider, userId_id, providerId_id, provider_qrcode_image, created_by_id, created_at, lastupdated_by_id, lastupdated_at) select '11111111', u.id, p.id, 'taozhang_weixi_pay_qrcode.jpg', 'sysop', now(), 'sysop',now() from users_user u, users_paymentprovider p where u.login_id='taozhang' and p.name='weixin';

insert into users_wallet (name, cryptocurrency_code_id, config_json, created_by_id, created_at, lastupdated_by_id, lastupdated_at) values('First','AXFund','', 'sysop', now(), 'sysop',now());

insert into users_userwallet (wallet_addr, user_id, wallet_id,created_by_id, created_at, lastupdated_by_id, lastupdated_at) select 'AHeeMMr4CqzxFTy3WGRgZnmE5ZoeyiA6vg', u.id, w.id, 'sysop', now(), 'sysop',now() from users_user u, users_wallet w where u.login_id='taozhang' and w.name='first';

insert into users_order (user_id, reference_wallet_id, order_type, sub_type, units, unit_price, unit_price_currency, status, cryptocurrencyId_id, created_by_id, created_at, lastupdated_by_id, lastupdated_at) select u.id, w.id , 'SELL', '', 1000.0, 1.02, 'CYN', 'OPEN', 'AXFund', 'sysop', now(), 'sysop',now() from users_user u, users_wallet w where u.login_id='taozhang' and w.name='first';
 
